"""
Orchestration of hand-offs between iterations: which agent takes a generated document next,
and whether any agent's output is ready, judged by the same bar in every iteration.
"""
from typing import Any, Dict, List, Optional

from app.agents import AGENTS, AGENT_MAP
from app.agents.base import BaseAgent
from app.core.quality import ids_in
from app.models.workflow import Artifact, StageEnum, WorkflowSession
from app.orchestration.orchestrator import savia_orchestrator
from app.orchestration.workflow_engine import workflow_engine

# An agent that declares it consumes this output outranks an equally relevant one that does not.
EDGE_BONUS = 0.35
# Jumping over a lifecycle stage (stories straight to TEST, past the design) costs this much per stage skipped.
SKIP_PENALTY = 0.4
STAGE_ORDER = [StageEnum.INGESTION, StageEnum.REQUIREMENTS, StageEnum.MOM, StageEnum.USER_STORY,
               StageEnum.DDL3, StageEnum.TESTING, StageEnum.COMPLETED]
# Sections that are correctly empty when the source has none of that item.
MAY_BE_EMPTY = {"attendees", "decisions_finalized", "open_questions", "dependencies", "action_items", "risks"}
MIN_FILLED = 0.6
MIN_CHARS = 300


def document_text(value: Any) -> str:
    """A generated document as readable text: the input to the next iteration. Mirrors the UI's sectionText."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join("• " + document_text(v).replace("\n", "\n  ") for v in value)
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if item in (None, "") or item == []:
                continue
            label = key.replace("_", " ")
            lines.append(f"{label[:1].upper()}{label[1:]}:{chr(10) if isinstance(item, list) else ' '}{document_text(item)}")
        return "\n".join(lines)
    return str(value)


async def next_agent(session: WorkflowSession, artifact: Artifact) -> Dict[str, Any]:
    """Reads the generated document and picks the agent that should take it next."""
    produced = set(workflow_engine.latest_artifacts(session.workflow_id))
    source = AGENT_MAP.get(artifact.agent_name)
    label = source.name if source else artifact.agent_name
    rec = await savia_orchestrator.recommend(
        session, raw_text=document_text(artifact.content), input_type="doc", filename=f"{label} output"
    )
    scored = {r["agent"]: r for r in rec["recommended_agents"]}

    candidates = []
    for agent in AGENTS:
        if agent.id in produced or agent.id == artifact.agent_name:
            continue
        confidence = scored.get(agent.id, {}).get("confidence", 0.0)
        builds_on = artifact.agent_name in agent.consumes
        if confidence <= 0 and not builds_on:
            continue
        # The next step follows the lifecycle: an agent two stages on needs the stage in between first.
        skipped = max(0, STAGE_ORDER.index(agent.stage) - STAGE_ORDER.index(source.stage) - 1) if source else 0
        score = confidence + (EDGE_BONUS if builds_on else 0.0) - SKIP_PENALTY * skipped
        candidates.append((score, agent, builds_on))
    candidates.sort(key=lambda c: -c[0])  # stable: ties keep lifecycle order

    if not candidates:
        return {"agent": None, "reason": "No other agent fits this document.", "recommendation": rec}

    _, chosen, builds_on = candidates[0]
    reason = scored.get(chosen.id, {}).get("reason") or f"{chosen.name} builds on the {label} output."
    order = [chosen.id] + [c[1].id for c in candidates[1:]]
    ranked = sorted(rec["recommended_agents"], key=lambda r: order.index(r["agent"]) if r["agent"] in order else len(order))
    return {
        "agent": chosen.id,
        "agent_name": chosen.name,
        "reason": reason,
        "confidence": scored.get(chosen.id, {}).get("confidence", 0.0),
        "builds_on_output": builds_on,
        "source_approved": artifact.approval_status.value == "approved",
        "alternatives": [c[1].id for c in candidates[1:3]],
        "source": rec.get("source"),
        # The recommendation the pages work from, with the chosen agent first.
        "recommendation": {**rec, "primary_agent": chosen.id, "recommended_agents": ranked},
    }


def check_handoff(session: WorkflowSession, source: Artifact, agent: BaseAgent) -> Optional[str]:
    """Why this agent must not take that output next, or None."""
    if source.workflow_id != session.workflow_id:
        return "That output belongs to a different workflow."
    if agent.id == source.agent_name:
        return f"{agent.name} produced this output; hand it to a different agent."
    if agent.id in workflow_engine.latest_artifacts(session.workflow_id):
        return f"{agent.name} has already run in this workflow."
    return None


def _filled(value: Any) -> bool:
    return value not in (None, "", [], {})


def readiness(agent: BaseAgent, content: Dict[str, Any], quality: Dict[str, Any], source: str, upstream: Dict[str, Any]) -> Dict[str, Any]:
    """One rubric for every agent in every iteration, so a later document is held to the first one's standard."""
    sections = [k for k in content if k not in MAY_BE_EMPTY]
    empty = [k for k in sections if not _filled(content[k])]
    ratio = (len(sections) - len(empty)) / len(sections) if sections else 0.0

    issues: List[str] = []
    if ratio < MIN_FILLED:
        issues.append(f"These sections are empty or missing: {', '.join(empty) or 'most of the document'}.")
    if len(document_text(content)) < MIN_CHARS:
        issues.append("The document is too thin to be useful; cover every point the input makes.")
    if quality.get("unsupported_figures"):
        issues.append(f"Remove figures that are not in the input: {', '.join(quality['unsupported_figures'][:5])}.")
    if quality.get("dangling_references"):
        issues.append(f"Remove references to IDs not in the input: {', '.join(quality['dangling_references'][:5])}.")
    # A document built on approved input must cite the IDs that input defines (REQ-, US-, DES-…) where they apply.
    own = tuple(agent.defines)
    known = {i for i in ids_in(source) | ids_in(upstream) if i.split("-")[0] not in own}
    if agent.consumes and known and not (ids_in(content) & known):
        issues.append(f"Reference the IDs the input defines ({', '.join(sorted(known)[:5])}…) where each one applies.")

    penalty = 0.2 * (len(issues) - (1 if ratio < MIN_FILLED else 0))
    return {"ready": not issues, "score": round(max(0.0, ratio * (1 - penalty)), 2), "issues": issues}
