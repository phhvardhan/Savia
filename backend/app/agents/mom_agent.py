import re
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.schemas import MomRaw
from app.models.workflow import StageEnum
from app.utils.logger import logger

SYSTEM = (
    "You are a senior business analyst writing Minutes of Meeting (MoM) from a transcript or notes.\n\n"
    "RULES:\n"
    "- Use only what the text says. Never invent people, owners, dates, decisions or figures.\n"
    "- If a field is not stated (e.g. an action has no due date), use null. Keep dates as written.\n"
    "- An empty list is correct when the meeting had none of that item.\n"
    "- decisions_finalized: only things the meeting explicitly agreed, not proposals.\n"
    "- open_questions: questions raised and left unanswered.\n"
    "- Text under [ANSWERS TO OPEN QUESTIONS] is confirmed by the user after the meeting: put each answer "
    "in key_points and into the decision or action it settles (e.g. an owner), and do not list it as open.\n\n"
    "Return only JSON in this shape:\n"
    '{"discussion_summary": str, '
    '"attendees": [{"name": str, "role": str|null}], '
    '"key_points": [str], "requirements_identified": [str], '
    '"decisions_finalized": [{"decision": str, "speaker": str|null, "context": str|null}], '
    '"action_items": [{"action": str, "assignee": str|null, "due_date": str|null, "speaker": str|null}], '
    '"open_questions": [str]}'
)


def _text(value: Any) -> Optional[str]:
    value = str(value).strip() if value is not None else ""
    return value if value and value.lower() not in ("null", "none", "n/a") else None


def _number_requirements(items: List[Any]) -> List[Any]:
    """REQ-001, REQ-002… so downstream agents can trace stories and designs back to a requirement."""
    out: List[Any] = []
    for idx, item in enumerate(items, start=1):
        text = item.strip() if isinstance(item, str) else None
        out.append(f"REQ-{idx:03d}: {text}" if text and not re.match(r"REQ-\d", text) else item)
    return out


class MomAgent(BaseAgent):
    id = "mom"
    name = "Minutes of Meeting (MoM) & Action Items Matrix"
    purpose = "Turns meeting transcripts, recordings or call notes into minutes, decisions and owned action items."
    stage = StageEnum.MOM
    defines = ("REQ",)  # it numbers the requirements, so those IDs are its own, not references
    output_model = MomRaw

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.source_text(input_data).strip():
            raise ValueError("Input text cannot be empty for the MOM Agent.")
        transcript = await self.source(input_data)
        logger.info(f"[MomAgent] Writing minutes from {len(transcript)} chars")
        raw = await self.generate(SYSTEM, transcript)

        def as_list(key: str) -> List[Any]:
            value = raw.get(key)
            return value if isinstance(value, list) else []

        decisions = []
        for idx, d in enumerate(as_list("decisions_finalized")):
            d = d if isinstance(d, dict) else {"decision": d}
            decisions.append({
                "decision_id": f"DEC-{idx + 1:03d}",
                "decision": _text(d.get("decision") or d.get("text")) or str(d),
                "speaker": _text(d.get("speaker")),
                "context": _text(d.get("context")),
            })

        actions = []
        for idx, a in enumerate(as_list("action_items")):
            a = a if isinstance(a, dict) else {"action": a}
            actions.append({
                "action_id": f"ACT-{idx + 1:03d}",
                "action": _text(a.get("action") or a.get("description")) or str(a),
                "assignee": _text(a.get("assignee") or a.get("owner")),
                "due_date": _text(a.get("due_date")),
                "speaker": _text(a.get("speaker")),
                "status": "Open",
            })

        return {
            "summary": _text(raw.get("discussion_summary")) or "",
            "attendees": [p if isinstance(p, dict) else {"name": str(p), "role": None} for p in as_list("attendees")],
            "key_points": as_list("key_points"),
            "requirements_identified": _number_requirements(as_list("requirements_identified")),
            "decisions_finalized": decisions,
            "action_items": actions,
            "open_questions": as_list("open_questions"),
        }


mom_agent = MomAgent()
