import json
from typing import List, Dict, Any
from app.models.workflow import WorkflowSession, StageEnum
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


ALL_AGENTS = [
    ("mom", "MOM & Action Items Agent", ["normalized_text"]),
    ("user-stories", "Agile User Stories & Backlog Epics Agent", ["approved_requirements_or_mom"]),
    ("gap-analysis", "Requirement Gap Analysis & Traceability Matrix (RTM) Agent", ["business_objectives_and_specs"]),
    ("ddl3", "DDL3 Design Agent", ["approved_user_stories_or_architecture"]),
    ("kdd-package", "KDD Package (Knowledge Design Document) for DAB Agent", ["architecture_design_doc"]),
    ("change-impact", "Change Impact Assessment & Interdependency Matrix Agent", ["current_and_target_architecture"]),
    ("test", "Test Automation & Inventory Agent", ["approved_design_or_user_stories"]),
    ("readiness-scoring", "Delivery Readiness Scoring & SDLC Audit Agent", ["deliverables_or_spec"]),
]

UNMATCHED_CONFIDENCE = 0.40

# What each agent produces, so the LLM chooses on purpose rather than on name.
AGENT_PURPOSES = {
    "mom": "Turns meeting transcripts, recordings or call notes into minutes, decisions and owned action items.",
    "user-stories": "Turns requirements, BRDs or meeting outcomes into INVEST user stories with Given/When/Then acceptance criteria.",
    "gap-analysis": "Compares requirements against what exists or is specified, producing a gap list and requirements traceability matrix (RTM).",
    "ddl3": "Writes or updates a DDL3 detailed functional/technical design document from approved stories or architecture input.",
    "kdd-package": "Assembles a Knowledge Design Document package for Design Authority Board (DAB) review from an architecture/design doc.",
    "change-impact": "Assesses the impact of a proposed change across systems and workstreams, producing an interdependency matrix.",
    "test": "Produces a test inventory and FIT/UAT test cases from approved designs or user stories.",
    "readiness-scoring": "Scores a deliverable or spec for delivery readiness and SDLC/GxP audit compliance, with remediation points.",
}

LLM_INPUT_CHARS = 9000
STAGE_VALUES = [s.value for s in StageEnum]

RECOMMENDER_SYSTEM = (
    "You are SAVIA, an assistant that reads what a delivery team has (a document, meeting transcript, "
    "or a typed description) and recommends which SDLC agent(s) they should run next, and why.\n\n"
    "AVAILABLE AGENTS (use these ids exactly):\n"
    + "\n".join(f"- {aid}: {AGENT_PURPOSES[aid]}" for aid, _, _ in ALL_AGENTS)
    + "\n\nRULES:\n"
    "1. Rank the 3 agents that best fit this input, best first. Always return exactly 3 when the input "
    "relates to software delivery, even if the 2nd or 3rd is a weak fit. Return an empty list only when "
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


class SaviaOrchestrator:
    """
    SAVIA Central Orchestrator & Agent Recommendation Layer.
    Analyzes normalized user input (Audio/Video/PDF/DOC/TXT), document titles,
    and SDLC context to recommend the optimal agent out of all 8 modular SDLC agents.
    """

    async def recommend(
        self,
        session: WorkflowSession,
        raw_text: str = None,
        input_type: str = None,
        filename: str = None,
    ) -> Dict[str, Any]:
        """LLM recommendation; falls back to keyword scoring if no provider answers."""
        try:
            return await self.recommend_with_llm(session, raw_text, input_type, filename)
        except Exception as e:
            logger.warning(f"[SAVIA Recommender] LLM unavailable ({e}); falling back to keyword scoring.")
            result = self.analyze_and_recommend(session, raw_text, input_type, filename)
            result["source"] = "keyword"
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
        # Only outputs with content; the session pre-creates empty slots for every stage.
        prior_outputs = sorted(k for k, v in (session.outputs or {}).items() if v) if session else []

        # ponytail: 9000 chars shared fairly across files; summarise per file if long inputs pick badly.
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
                continue  # unknown id or duplicate from the model
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
            if len(recommended) == 3:
                break

        if not recommended and not isinstance(data.get("recommendations"), list):
            raise ValueError(f"LLM reply had no recommendations list: {json.dumps(data)[:300]}")

        # An empty list is a real answer ("nothing fits yet"), not a failure.
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

        # Extract document name / filename from argument, session title, or source documents
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

        scores: Dict[str, float] = {
            "mom": 0.0,
            "user-stories": 0.0,
            "gap-analysis": 0.0,
            "ddl3": 0.0,
            "kdd-package": 0.0,
            "change-impact": 0.0,
            "test": 0.0,
            "readiness-scoring": 0.0,
        }

        reasons: Dict[str, str] = {}

        # ---------------------------------------------------------------------
        # 1. FILENAME MATCHING (Heavy weight if document explicitly named)
        # ---------------------------------------------------------------------
        if doc_name_lower:
            # DDL3 Design Document
            if any(k in doc_name_lower for k in [
                "ddl3", "ddl_3", "detailed_design", "design_spec", "functional_spec",
                "technical_spec", "architecture_spec", "fad", "tad", "design_doc",
                "design_specification", "detailed_spec"
            ]):
                scores["ddl3"] += 30.0
                reasons["ddl3"] = f"Document '{doc_name}' is a DDL3 Design & Technical Architecture Specification."

            # Test Document
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

            # Agile User Stories
            if any(k in doc_name_lower for k in [
                "user_stories", "user_story", "stories", "backlog", "jira", "epics", "brd", "prd"
            ]):
                scores["user-stories"] += 30.0
                reasons["user-stories"] = f"Document '{doc_name}' indicates Agile User Stories & Backlog Epics."

            # Meeting Minutes
            if any(k in doc_name_lower for k in [
                "mom", "minutes", "transcript", "meeting", "recording", "call_notes", "discussion"
            ]):
                scores["mom"] += 30.0
                reasons["mom"] = f"Document '{doc_name}' indicates a Meeting Transcript or Minutes of Meeting."

            # Readiness & Audit
            if any(k in doc_name_lower for k in [
                "readiness", "scorecard", "audit", "sdlc_audit", "quality_gate", "gxp_audit"
            ]):
                scores["readiness-scoring"] += 30.0
                reasons["readiness-scoring"] = f"Document '{doc_name}' indicates a Delivery Readiness Audit or Quality Scorecard."

            # Gap Analysis
            if any(k in doc_name_lower for k in [
                "gap_analysis", "rtm", "traceability_matrix", "fit_gap"
            ]):
                scores["gap-analysis"] += 30.0
                reasons["gap-analysis"] = f"Document '{doc_name}' indicates a Requirement Gap Analysis & RTM."

            # Change Impact
            if any(k in doc_name_lower for k in [
                "change_impact", "impact_assessment", "interdependency"
            ]):
                scores["change-impact"] += 30.0
                reasons["change-impact"] = f"Document '{doc_name}' indicates a Change Impact Assessment & Interdependency Matrix."

            # KDD Package
            if any(k in doc_name_lower for k in [
                "kdd", "dab", "design_authority", "architecture_dossier"
            ]):
                scores["kdd-package"] += 30.0
                reasons["kdd-package"] = f"Document '{doc_name}' indicates a KDD Package for Design Authority Board review."

        # ---------------------------------------------------------------------
        # 2. INPUT TYPE SIGNALS
        # ---------------------------------------------------------------------
        if i_type in ["audio", "video"]:
            scores["mom"] += 35.0
            reasons["mom"] = "The input consists of audio/video recording best suited for Minutes of Meeting and action item extraction."

        # ---------------------------------------------------------------------
        # 3. CONTENT SIGNATURE PHRASES & KEYWORDS
        # ---------------------------------------------------------------------
        def count_matches(keywords: List[str]) -> int:
            return sum(1 for kw in keywords if kw in text_lower)

        # MOM
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

        # Agile User Stories
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
            scores["user-stories"] += story_sig_count * 7.0 + story_sup_count * 2.0
            if "user-stories" not in reasons:
                reasons["user-stories"] = "The requirement context contains functional capabilities suitable for INVEST user stories and BDD acceptance criteria."

        # DDL3 Design
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

        # Test Automation & Inventory
        # Notice: Only count genuine test markers (not isolated words like "validation" or "scenario" which belong to design)
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

        # Readiness Scoring & SDLC Audit
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
            scores["readiness-scoring"] += read_sig_count * 7.0 + read_sup_count * 2.0
            if "readiness-scoring" not in reasons:
                reasons["readiness-scoring"] = "The input contains deliverables requiring multi-dimensional quality scorecards, GxP compliance audit, and readiness scoring."

        # Gap Analysis & RTM
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

        # Change Impact Assessment
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

        # KDD Package for DAB
        kdd_signatures = [
            "knowledge design document", "kdd package", "design authority board",
            "dab review", "architecture dossier", "architectural decision record", "adr"
        ]
        kdd_supporting = ["kdd", "dab", "governance dossier", "solution rationale", "board review"]
        kdd_sig_count = count_matches(kdd_signatures)
        kdd_sup_count = count_matches(kdd_supporting)
        if kdd_sig_count > 0 or kdd_sup_count >= 2:
            scores["kdd-package"] += kdd_sig_count * 7.0 + kdd_sup_count * 2.0
            if "kdd-package" not in reasons:
                reasons["kdd-package"] = "The input involves architecture governance dossiers tailored for Design Authority Board (DAB) review."

        # Upstream / downstream pipeline stage synergy
        if session and session.outputs:
            if session.outputs.get("mom") and scores["user-stories"] > 0:
                scores["user-stories"] += 5.0
            if session.outputs.get("user_stories") and scores["ddl3"] > 0:
                scores["ddl3"] += 5.0
            if session.outputs.get("ddl3") and scores["test"] > 0:
                scores["test"] += 5.0

        # Build list of matching agents
        agent_names = {a[0]: a[1] for a in ALL_AGENTS}
        agent_inputs = {a[0]: a[2] for a in ALL_AGENTS}

        # Lifecycle companion agents to ensure all 3 recommendation cards are populated
        LIFECYCLE_COMPANIONS: Dict[str, List[tuple]] = {
            "ddl3": [
                ("user-stories", "Agile User Stories & Backlog Epics Agent", "Stories and BDD criteria upstream of design specification", 0.93),
                ("test", "Test Automation & Inventory Agent", "Test inventory and FIT/UAT test cases downstream of design", 0.91),
                ("kdd-package", "KDD Package for DAB Agent", "Architecture governance and design authority review", 0.88),
            ],
            "test": [
                ("ddl3", "DDL3 Design Agent", "Technical architecture and functional design baseline", 0.93),
                ("user-stories", "Agile User Stories & Backlog Epics Agent", "User stories and BDD criteria for test verification", 0.91),
                ("readiness-scoring", "Delivery Readiness Scoring & SDLC Audit Agent", "Verify test coverage against delivery quality gates", 0.88),
            ],
            "user-stories": [
                ("ddl3", "DDL3 Design Agent", "Detailed design and architecture specification downstream", 0.93),
                ("test", "Test Automation & Inventory Agent", "Test inventory and acceptance criteria verification", 0.91),
                ("mom", "MOM & Action Items Agent", "Discussion context and stakeholder requirements baseline", 0.88),
            ],
            "mom": [
                ("user-stories", "Agile User Stories & Backlog Epics Agent", "Decompose meeting outcomes into INVEST user stories", 0.93),
                ("gap-analysis", "Requirement Gap Analysis & Traceability Matrix (RTM) Agent", "Identify requirements gaps from discussion notes", 0.91),
                ("ddl3", "DDL3 Design Agent", "Architecture and design specifications discussed in meeting", 0.88),
            ],
            "readiness-scoring": [
                ("test", "Test Automation & Inventory Agent", "Audit test suite execution results and code coverage", 0.93),
                ("ddl3", "DDL3 Design Agent", "Evaluate technical design deliverables against SDLC quality gates", 0.91),
                ("gap-analysis", "Requirement Gap Analysis & RTM Agent", "Traceability audit across requirements and artifacts", 0.88),
            ],
            "gap-analysis": [
                ("user-stories", "Agile User Stories & Backlog Epics Agent", "Trace gap items back to user story backlog", 0.93),
                ("ddl3", "DDL3 Design Agent", "Verify technical architecture addresses requirement gaps", 0.91),
                ("readiness-scoring", "Delivery Readiness Scoring & SDLC Audit Agent", "Audit delivery readiness against unmet requirements", 0.88),
            ],
            "change-impact": [
                ("ddl3", "DDL3 Design Agent", "Evaluate target architecture and component modifications", 0.93),
                ("test", "Test Automation & Inventory Agent", "Plan regression testing for impacted workstreams", 0.91),
                ("kdd-package", "KDD Package for DAB Agent", "Architecture decision dossier for impacted systems", 0.88),
            ],
            "kdd-package": [
                ("ddl3", "DDL3 Design Agent", "Source functional and technical design specifications", 0.93),
                ("change-impact", "Change Impact Assessment & Interdependency Matrix Agent", "Evaluate architectural change dependencies for board", 0.91),
                ("readiness-scoring", "Delivery Readiness Scoring & SDLC Audit Agent", "Audit governance readiness for DAB sign-off", 0.88),
            ],
        }

        # Filter agents that have a positive score
        positive_agents = [(aid, scores[aid]) for aid in scores if scores[aid] > 0]
        positive_agents.sort(key=lambda x: x[1], reverse=True)

        recommended_agents = []

        if positive_agents:
            top_agent, top_score = positive_agents[0]

            for aid, score in positive_agents:
                # Relative confidence: top agent gets 0.95 - 0.98, runners up get proportional confidence
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
            # Fallback if no keywords matched
            top_agent = "mom"
            recommended_agents.append({
                "agent": "mom",
                "agent_name": "MOM & Action Items Agent",
                "reason": "Defaulting to MOM & Requirement Understanding for document ingestion.",
                "required_inputs": ["normalized_text"],
                "confidence": 0.95,
                "matched": True,
            })

        # Ensure we always have at least 3 matched agents so all 3 cards in the UI render properly
        matched_ids = {entry["agent"] for entry in recommended_agents}
        companions = LIFECYCLE_COMPANIONS.get(top_agent, LIFECYCLE_COMPANIONS["ddl3"])

        for comp_id, comp_name, comp_reason, comp_conf in companions:
            if len([a for a in recommended_agents if a.get("matched")]) >= 3:
                break
            if comp_id not in matched_ids:
                recommended_agents.append({
                    "agent": comp_id,
                    "agent_name": comp_name,
                    "reason": comp_reason,
                    "required_inputs": agent_inputs.get(comp_id, ["normalized_text"]),
                    "confidence": comp_conf,
                    "matched": True,
                })
                matched_ids.add(comp_id)

        # Re-sort so top agent is always #1 and confidences descend cleanly
        recommended_agents.sort(key=lambda x: (x.get("matched", False), x.get("confidence", 0)), reverse=True)
        primary_recommendation = recommended_agents[0]

        # Add remaining unmatched agents with low confidence so UI can show fuller plan if needed
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
