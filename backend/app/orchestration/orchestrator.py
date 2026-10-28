import hashlib
import json
from collections import OrderedDict
from typing import Any, Dict, List

from app.agents import AGENT_MAP, AGENTS
from app.core.llm import call_llm
from app.core.text import fit_text
from app.models.workflow import StageEnum, WorkflowSession
from app.utils.logger import logger


ALL_AGENTS = [(agent.id, agent.name, agent.required_inputs) for agent in AGENTS]

UNMATCHED_CONFIDENCE = 0.40

AGENT_PURPOSES = {agent.id: agent.purpose for agent in AGENTS}

LLM_INPUT_CHARS = 16000
CACHE_SIZE = 64
STAGE_VALUES = [s.value for s in StageEnum]

RECOMMENDER_SYSTEM = (
    "You are SAVIA, an assistant that reads what a delivery team has (a document, meeting transcript, "
    "or a typed description) and recommends which SDLC agent(s) they should run next, and why.\n\n"
    "AVAILABLE AGENTS (use these ids exactly):\n"
    + "\n".join(f"- {aid}: {AGENT_PURPOSES[aid]}" for aid, _, _ in ALL_AGENTS)
    + "\n\nRULES:\n"
    "1. Rank the 5 agents that best fit this input, best first. Always return exactly 5 when the input "
    "relates to software delivery, even if the later ones are weak fits. Return an empty list only when "
    "the input is unrelated to software delivery or too empty to judge.\n"
    "2. confidence is your honest 0.0-1.0 estimate that each agent fits. Weaker fits get low values "
    "(e.g. 0.2-0.5); do not inflate them to look good. If the input is vague, say what is missing.\n"
    "3. reason: one or two sentences, specific to this input (quote or name what you saw). "
    "No generic descriptions of the agent.\n"
    "4. next_step: one short sentence telling the user how to use the top agent with what they gave. "
    "Plain text, no markdown; name agents in words (e.g. 'the MOM agent'), not by id.\n"
    f"5. lifecycle_stage: where this input sits, one of {STAGE_VALUES}.\n"
    "6. missing_information: things the user should add for a better result (empty list if none).\n\n"
    "Return only JSON in this shape:\n"
    '{"recommendations": [{"agent": "<id>", "confidence": 0.0, "reason": "..."}], '
    '"next_step": "...", "lifecycle_stage": "...", "missing_information": ["..."]}'
)


def build_plan(recommended: List[Dict[str, Any]], produced: List[str]) -> List[Dict[str, Any]]:
    chosen = [r["agent"] for r in recommended if r.get("matched") and r.get("confidence", 0) >= UNMATCHED_CONFIDENCE]
    if not chosen and recommended and recommended[0].get("matched"):
        chosen = [recommended[0]["agent"]]
    ordered: List[str] = []

    def visit(agent_id: str, trail: tuple) -> None:
        if agent_id in ordered or agent_id in trail:
            return
        for dep in AGENT_MAP[agent_id].consumes:
            if dep in chosen:
                visit(dep, trail + (agent_id,))
        ordered.append(agent_id)

    for agent_id in chosen:
        visit(agent_id, ())
    return [
        {
            "step": i + 1,
            "agent": agent_id,
            "agent_name": AGENT_MAP[agent_id].name,
            "after": [d for d in AGENT_MAP[agent_id].consumes if d in ordered[:i]],
            "uses_existing": [d for d in AGENT_MAP[agent_id].consumes if d in produced],
            "approval_needed_before_next": any(agent_id in AGENT_MAP[o].consumes for o in ordered[i + 1:]),
        }
        for i, agent_id in enumerate(ordered)
    ]


class SaviaOrchestrator:
    def __init__(self):
        self._cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    async def recommend(
        self,
        session: WorkflowSession,
        raw_text: str = None,
        input_type: str = None,
        filename: str = None,
    ) -> Dict[str, Any]:
        text = raw_text or (session.normalized_input if session else "") or ""
        produced = sorted(k for k, v in (session.outputs or {}).items() if v) if session else []
        key = hashlib.sha256(json.dumps([text, input_type, filename, produced]).encode("utf-8")).hexdigest()
        if key in self._cache:
            self._cache.move_to_end(key)
            return {**self._cache[key], "workflow_id": session.workflow_id if session else None}
        try:
            result = await self.recommend_with_llm(session, raw_text, input_type, filename)
        except Exception as e:
            logger.warning(f"[SAVIA Recommender] LLM unavailable ({e}); falling back to keyword scoring.")
            result = self.analyze_and_recommend(session, raw_text, input_type, filename)
            result["source"] = "keyword"
        result["plan"] = build_plan(result["recommended_agents"], produced)
        if result["source"] == "llm":
            self._cache[key] = result
            if len(self._cache) > CACHE_SIZE:
                self._cache.popitem(last=False)
        return result

    async def recommend_with_llm(
        self,
        session: WorkflowSession,
        raw_text: str = None,
        input_type: str = None,
        filename: str = None,
    ) -> Dict[str, Any]:
        text = raw_text or (session.normalized_input if session else "") or ""
        i_type = input_type or (session.input_type if session else "unknown")
        prior_outputs = sorted(k for k, v in (session.outputs or {}).items() if v) if session else []

        user = (
            f"FILENAME: {filename or '(typed by the user)'}\n"
            f"INPUT TYPE: {i_type}\n"
            f"ALREADY PRODUCED IN THIS WORKFLOW: {', '.join(prior_outputs) or 'nothing yet'}\n"
            f"INPUT ({len(text)} chars{', truncated' if len(text) > LLM_INPUT_CHARS else ''}):\n"
            f"{fit_text(text, LLM_INPUT_CHARS)}"
        )
        data = await call_llm(RECOMMENDER_SYSTEM, user, expected_type=dict)

        agent_names = {a[0]: a[1] for a in ALL_AGENTS}
        agent_inputs = {a[0]: a[2] for a in ALL_AGENTS}

        recommended: List[Dict[str, Any]] = []
        for item in data.get("recommendations") or []:
            aid = str(item.get("agent", "")).strip()
            if aid not in agent_names or any(r["agent"] == aid for r in recommended):
                continue
            try:
                conf = float(item.get("confidence", 0))
            except (TypeError, ValueError):
                conf = 0.0
            recommended.append({
                "agent": aid,
                "agent_name": agent_names[aid],
                "reason": str(item.get("reason") or "").strip() or f"Fits {agent_names[aid]}.",
                "required_inputs": agent_inputs[aid],
                "confidence": round(min(max(conf, 0.0), 1.0), 2),
                "matched": True,
            })
            if len(recommended) == 5:
                break

        if not recommended and not isinstance(data.get("recommendations"), list):
            raise ValueError(f"LLM reply had no recommendations list: {json.dumps(data)[:300]}")

        recommended.sort(key=lambda r: r["confidence"], reverse=True)
        primary = recommended[0] if recommended else None

        for aid, name, inputs in ALL_AGENTS:
            if not any(r["agent"] == aid for r in recommended):
                recommended.append({
                    "agent": aid,
                    "agent_name": name,
                    "reason": "Not a fit for this input; available if you want it in the plan.",
                    "required_inputs": inputs,
                    "confidence": 0.0,
                    "matched": False,
                })

        stage = str(data.get("lifecycle_stage") or "").strip().lower()
        if stage not in STAGE_VALUES:
            stage = (session.current_stage if session else StageEnum.INGESTION).value

        missing = [str(m) for m in (data.get("missing_information") or []) if str(m).strip()]

        logger.info(
            f"[SAVIA Recommender] LLM picked {[(r['agent'], r['confidence']) for r in recommended if r['matched']]}"
        )
        return {
            "workflow_id": session.workflow_id if session else None,
            "input_type": i_type,
            "current_stage": stage,
            "recommended_agents": recommended,
            "primary_agent": primary["agent"] if primary else "",
            "primary_reason": primary["reason"] if primary else "No agent fits this input yet.",
            "missing_information": missing,
            "next_action": str(data.get("next_step") or "").replace("**", "").strip() or "await_user_confirmation",
            "source": "llm",
        }

    def analyze_and_recommend(
        self,
        session: WorkflowSession,
        raw_text: str = None,
        input_type: str = None,
        filename: str = None
    ) -> Dict[str, Any]:
        text = raw_text or (session.normalized_input if session else "") or ""
        text_lower = text.lower()
        i_type = input_type or (session.input_type if session else "unknown")
        current_stage = session.current_stage if session else StageEnum.INGESTION

        doc_name = filename or ""
        if not doc_name and session:
            if session.title and "Workflow - " in session.title:
                doc_name = session.title.replace("Workflow - ", "").strip()
            elif session.source_documents and len(session.source_documents) > 0:
                doc_name = session.source_documents[0].get("filename", "")
        doc_name_lower = doc_name.lower()

        logger.info(
            f"[SAVIA Orchestrator] Analyzing input: len={len(text)}, doc='{doc_name}', "
            f"type='{i_type}', stage='{current_stage.value}'"
        )

        scores: Dict[str, float] = {aid: 0.0 for aid, _, _ in ALL_AGENTS}

        reasons: Dict[str, str] = {}

        if doc_name_lower:
            if any(k in doc_name_lower for k in [
                "ddl3", "ddl_3", "detailed_design", "design_spec", "functional_spec",
                "technical_spec", "architecture_spec", "fad", "tad", "design_doc",
                "design_specification", "detailed_spec"
            ]):
                scores["ddl3"] += 30.0
                reasons["ddl3"] = f"Document '{doc_name}' is a DDL3 Design & Technical Architecture Specification."

            if any(k in doc_name_lower for k in [
                "test_case", "test_plan", "test_suite", "test_inventory", "test_spec",
                "qa_plan", "uat_plan", "fit_plan", "manual_test", "test_matrix"
            ]):
                scores["test"] += 30.0
                reasons["test"] = f"Document '{doc_name}' is a Test Plan / Test Case Matrix specification."
            elif (
                doc_name_lower.startswith("test") or
                "_test." in doc_name_lower or
                "-test." in doc_name_lower
            ):
                scores["test"] += 18.0
                reasons["test"] = f"Document '{doc_name}' indicates test deliverables."

            if any(k in doc_name_lower for k in [
                "user_stories", "user_story", "stories", "backlog", "jira", "epics", "brd", "prd"
            ]):
                scores["agile-stories"] += 30.0
                reasons["agile-stories"] = f"Document '{doc_name}' indicates Agile User Stories & Backlog Epics."

            if any(k in doc_name_lower for k in [
                "mom", "minutes", "transcript", "meeting", "recording", "call_notes", "discussion"
            ]):
                scores["mom"] += 30.0
                reasons["mom"] = f"Document '{doc_name}' indicates a Meeting Transcript or Minutes of Meeting."

            if any(k in doc_name_lower for k in [
                "readiness", "scorecard", "audit", "sdlc_audit", "quality_gate", "gxp_audit"
            ]):
                scores["readiness-audit"] += 30.0
                reasons["readiness-audit"] = f"Document '{doc_name}' indicates a Delivery Readiness Audit or Quality Scorecard."

            if any(k in doc_name_lower for k in [
                "gap_analysis", "rtm", "traceability_matrix", "fit_gap"
            ]):
                scores["gap-analysis"] += 30.0
                reasons["gap-analysis"] = f"Document '{doc_name}' indicates a Requirement Gap Analysis & RTM."

            if any(k in doc_name_lower for k in [
                "change_impact", "impact_assessment", "interdependency"
            ]):
                scores["change-impact"] += 30.0
                reasons["change-impact"] = f"Document '{doc_name}' indicates a Change Impact Assessment & Interdependency Matrix."

            if any(k in doc_name_lower for k in [
                "kdd", "dab", "design_authority", "architecture_dossier"
            ]):
                scores["kdd-dab"] += 30.0
                reasons["kdd-dab"] = f"Document '{doc_name}' indicates a KDD Package for Design Authority Board review."

        if i_type in ["audio", "video"]:
            scores["mom"] += 35.0
            reasons["mom"] = "The input consists of audio/video recording best suited for Minutes of Meeting and action item extraction."

        def count_matches(keywords: List[str]) -> int:
            return sum(1 for kw in keywords if kw in text_lower)

        mom_signatures = [
            "meeting transcript", "minutes of meeting", "meeting minutes",
            "meeting attendees", "meeting date", "action items:", "speaker 1:",
            "speaker 2:", "call notes", "discussion summary"
        ]
        mom_supporting = [
            "transcript", "attendees", "speaker", "workshop", "agenda",
            "discussion", "action item", "meeting"
        ]
        mom_sig_count = count_matches(mom_signatures)
        mom_sup_count = count_matches(mom_supporting)
        if mom_sig_count > 0 or mom_sup_count >= 2:
            scores["mom"] += mom_sig_count * 7.0 + mom_sup_count * 2.0
            if "mom" not in reasons:
                reasons["mom"] = "The input consists of discussion text best suited for Minutes of Meeting and action item extraction."

        story_signatures = [
            "as a ", "i want to ", "so that ", "user story", "acceptance criteria",
            "given ", "when ", "then ", "invest criteria", "sprint backlog", "epic:"
        ]
        story_supporting = [
            "user stories", "epic", "backlog", "feature", "sprint",
            "story points", "definition of done", "requirement"
        ]
        story_sig_count = count_matches(story_signatures)
        story_sup_count = count_matches(story_supporting)
        if story_sig_count > 0 or story_sup_count >= 2:
            scores["agile-stories"] += story_sig_count * 7.0 + story_sup_count * 2.0
            if "agile-stories" not in reasons:
                reasons["agile-stories"] = "The requirement context contains functional capabilities suitable for INVEST user stories and BDD acceptance criteria."

        ddl3_signatures = [
            "ddl3", "detailed design", "technical design", "functional design",
            "system architecture", "database schema", "table definition",
            "data derivation", "interface specification", "api specification",
            "wrief", "ricefw", "business rules", "validation rules",
            "error handling matrix", "entity relationship", "technical spec",
            "component architecture"
        ]
        ddl3_supporting = [
            "architecture", "data model", "data flow", "derivation", "component",
            "integration", "payload", "fiori", "s/4hana", "custom abap", "design"
        ]
        ddl3_sig_count = count_matches(ddl3_signatures)
        ddl3_sup_count = count_matches(ddl3_supporting)
        if ddl3_sig_count > 0 or ddl3_sup_count >= 2:
            scores["ddl3"] += ddl3_sig_count * 7.0 + ddl3_sup_count * 2.0
            if "ddl3" not in reasons:
                reasons["ddl3"] = "The input specifies architecture, technical specifications, or functional components suited for Design Document Lifecycle (DDL3) management."

        test_signatures = [
            "test case id", "test cases matrix", "test execution plan", "test inventory",
            "manual test cases", "test steps:", "expected result:", "actual result:",
            "fit testing", "uat testing", "preconditions:", "pass/fail criteria",
            "test script", "test suite"
        ]
        test_supporting = [
            "test case", "test cases", "test plan", "test data", "qa execution",
            "qa verification", "regression test", "defect severity", "uat"
        ]
        test_sig_count = count_matches(test_signatures)
        test_sup_count = count_matches(test_supporting)
        if test_sig_count > 0 or test_sup_count >= 2:
            scores["test"] += test_sig_count * 7.0 + test_sup_count * 2.0
            if "test" not in reasons:
                reasons["test"] = "The available requirements/design artifacts permit end-to-end FIT/UAT test inventory generation, manual test cases, and scenario stitching."

        readiness_signatures = [
            "delivery readiness", "readiness score", "readiness scorecard",
            "sdlc audit", "quality gate", "gxp compliance audit", "audit findings",
            "remediation plan", "sdlc audit report", "readiness scoring"
        ]
        readiness_supporting = [
            "readiness", "scorecard", "audit", "compliance", "hypercare",
            "gate criteria", "feasibility", "gxp"
        ]
        read_sig_count = count_matches(readiness_signatures)
        read_sup_count = count_matches(readiness_supporting)
        if read_sig_count > 0 or read_sup_count >= 2:
            scores["readiness-audit"] += read_sig_count * 7.0 + read_sup_count * 2.0
            if "readiness-audit" not in reasons:
                reasons["readiness-audit"] = "The input contains deliverables requiring multi-dimensional quality scorecards, GxP compliance audit, and readiness scoring."

        gap_signatures = [
            "requirements traceability matrix", "rtm", "gap analysis",
            "requirement gap", "standard vs custom gap", "unmet requirement",
            "traceability matrix"
        ]
        gap_supporting = ["traceability", "custom gap", "standard gap", "fit/gap", "gap"]
        gap_sig_count = count_matches(gap_signatures)
        gap_sup_count = count_matches(gap_supporting)
        if gap_sig_count > 0 or gap_sup_count >= 2:
            scores["gap-analysis"] += gap_sig_count * 7.0 + gap_sup_count * 2.0
            if "gap-analysis" not in reasons:
                reasons["gap-analysis"] = "The input requires requirement traceability mapping (RTM) and standard vs custom gap analysis."

        impact_signatures = [
            "change impact assessment", "interdependency matrix", "cross-platform impact",
            "system decommission", "blast radius", "workstream dependency"
        ]
        impact_supporting = ["change impact", "interdependency", "legacy migration", "upstream systems", "downstream systems", "impact"]
        impact_sig_count = count_matches(impact_signatures)
        impact_sup_count = count_matches(impact_supporting)
        if impact_sig_count > 0 or impact_sup_count >= 2:
            scores["change-impact"] += impact_sig_count * 7.0 + impact_sup_count * 2.0
            if "change-impact" not in reasons:
                reasons["change-impact"] = "The input demands cross-platform impact analysis and interdependency matrix evaluation."

        solution_signatures = [
            "problem statement", "solution blueprint", "solution design", "proposed solution",
            "solution options", "how should we solve", "pain point"
        ]
        solution_supporting = ["problem", "solution", "pain", "challenge", "root cause", "improve"]
        sol_sig_count = count_matches(solution_signatures)
        sol_sup_count = count_matches(solution_supporting)
        if sol_sig_count > 0 or sol_sup_count >= 3:
            scores["solution-analyzer"] += sol_sig_count * 7.0 + sol_sup_count * 2.0
            if "solution-analyzer" not in reasons:
                reasons["solution-analyzer"] = "The input describes a problem that needs a proposed solution design."

        kdd_signatures = [
            "knowledge design document", "kdd package", "design authority board",
            "dab review", "architecture dossier", "architectural decision record", "adr"
        ]
        kdd_supporting = ["kdd", "dab", "governance dossier", "solution rationale", "board review"]
        kdd_sig_count = count_matches(kdd_signatures)
        kdd_sup_count = count_matches(kdd_supporting)
        if kdd_sig_count > 0 or kdd_sup_count >= 2:
            scores["kdd-dab"] += kdd_sig_count * 7.0 + kdd_sup_count * 2.0
            if "kdd-dab" not in reasons:
                reasons["kdd-dab"] = "The input involves architecture governance dossiers tailored for Design Authority Board (DAB) review."

        if session and session.outputs:
            if session.outputs.get("mom") and scores["agile-stories"] > 0:
                scores["agile-stories"] += 5.0
            if session.outputs.get("agile-stories") and scores["ddl3"] > 0:
                scores["ddl3"] += 5.0
            if session.outputs.get("ddl3") and scores["test"] > 0:
                scores["test"] += 5.0

        agent_names = {a[0]: a[1] for a in ALL_AGENTS}
        agent_inputs = {a[0]: a[2] for a in ALL_AGENTS}

        LIFECYCLE_COMPANIONS: Dict[str, List[tuple]] = {
            "solution-analyzer": [
                ("change-impact", "Assess the impact of the proposed solution on current systems", 0.93),
                ("agile-stories", "Break the agreed solution into user stories", 0.91),
                ("kdd-dab", "Take the solution design to the Design Authority Board", 0.88),
            ],
            "ddl3": [
                ("agile-stories", "Stories and BDD criteria upstream of design specification", 0.93),
                ("test", "Test inventory and FIT/UAT test cases downstream of design", 0.91),
                ("kdd-dab", "Architecture governance and design authority review", 0.88),
            ],
            "test": [
                ("ddl3", "Technical architecture and functional design baseline", 0.93),
                ("agile-stories", "User stories and BDD criteria for test verification", 0.91),
                ("readiness-audit", "Verify test coverage against delivery quality gates", 0.88),
            ],
            "agile-stories": [
                ("ddl3", "Detailed design and architecture specification downstream", 0.93),
                ("test", "Test inventory and acceptance criteria verification", 0.91),
                ("mom", "Discussion context and stakeholder requirements baseline", 0.88),
            ],
            "mom": [
                ("agile-stories", "Decompose meeting outcomes into INVEST user stories", 0.93),
                ("gap-analysis", "Identify requirements gaps from discussion notes", 0.91),
                ("ddl3", "Architecture and design specifications discussed in meeting", 0.88),
            ],
            "readiness-audit": [
                ("test", "Audit test suite execution results and code coverage", 0.93),
                ("ddl3", "Evaluate technical design deliverables against SDLC quality gates", 0.91),
                ("gap-analysis", "Traceability audit across requirements and artifacts", 0.88),
            ],
            "gap-analysis": [
                ("agile-stories", "Trace gap items back to user story backlog", 0.93),
                ("ddl3", "Verify technical architecture addresses requirement gaps", 0.91),
                ("readiness-audit", "Audit delivery readiness against unmet requirements", 0.88),
            ],
            "change-impact": [
                ("ddl3", "Evaluate target architecture and component modifications", 0.93),
                ("test", "Plan regression testing for impacted workstreams", 0.91),
                ("kdd-dab", "Architecture decision dossier for impacted systems", 0.88),
            ],
            "kdd-dab": [
                ("ddl3", "Source functional and technical design specifications", 0.93),
                ("change-impact", "Evaluate architectural change dependencies for board", 0.91),
                ("readiness-audit", "Audit governance readiness for DAB sign-off", 0.88),
            ],
        }

        positive_agents = [(aid, scores[aid]) for aid in scores if scores[aid] > 0]
        positive_agents.sort(key=lambda x: x[1], reverse=True)

        recommended_agents = []

        if positive_agents:
            top_agent, top_score = positive_agents[0]

            for aid, score in positive_agents:
                if aid == top_agent:
                    conf = min(0.98, 0.95 + 0.03 * min(1.0, top_score / 40.0))
                else:
                    ratio = score / max(top_score, 1.0)
                    conf = round(0.70 + (0.24 * ratio), 2)

                recommended_agents.append({
                    "agent": aid,
                    "agent_name": agent_names.get(aid, aid),
                    "reason": reasons.get(aid, f"Input matches criteria for {agent_names.get(aid, aid)}."),
                    "required_inputs": agent_inputs.get(aid, ["normalized_text"]),
                    "confidence": round(conf, 2),
                    "matched": True,
                })
        else:
            top_agent = "mom"
            recommended_agents.append({
                "agent": "mom",
                "agent_name": agent_names["mom"],
                "reason": "Defaulting to MOM & Requirement Understanding for document ingestion.",
                "required_inputs": ["normalized_text"],
                "confidence": 0.95,
                "matched": True,
            })

        matched_ids = {entry["agent"] for entry in recommended_agents}
        companions = LIFECYCLE_COMPANIONS.get(top_agent, LIFECYCLE_COMPANIONS["ddl3"])

        for comp_id, comp_reason, comp_conf in companions:
            if len([a for a in recommended_agents if a.get("matched")]) >= 5:
                break
            if comp_id not in matched_ids:
                recommended_agents.append({
                    "agent": comp_id,
                    "agent_name": agent_names[comp_id],
                    "reason": comp_reason,
                    "required_inputs": agent_inputs.get(comp_id, ["normalized_text"]),
                    "confidence": comp_conf,
                    "matched": True,
                })
                matched_ids.add(comp_id)

        recommended_agents.sort(key=lambda x: (x.get("matched", False), x.get("confidence", 0)), reverse=True)
        primary_recommendation = recommended_agents[0]

        all_matched_ids = {entry["agent"] for entry in recommended_agents}
        for agent_id, agent_name, required_inputs in ALL_AGENTS:
            if agent_id in all_matched_ids:
                continue
            recommended_agents.append({
                "agent": agent_id,
                "agent_name": agent_name,
                "reason": "No direct signal for this agent in the input; available if you want it in the plan.",
                "required_inputs": required_inputs,
                "confidence": UNMATCHED_CONFIDENCE,
                "matched": False,
            })

        return {
            "workflow_id": session.workflow_id if session else None,
            "input_type": i_type,
            "current_stage": current_stage.value,
            "recommended_agents": recommended_agents,
            "primary_agent": primary_recommendation["agent"],
            "primary_reason": primary_recommendation["reason"],
            "missing_information": [],
            "next_action": "await_user_confirmation",
        }


savia_orchestrator = SaviaOrchestrator()
