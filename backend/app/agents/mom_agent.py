from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgent
from app.models.workflow import StageEnum
from app.core.agent import generate_mom
from app.utils.logger import logger


class MomAgent(BaseAgent):
    id = "mom"
    name = "Minutes of Meeting (MoM) & Action Items Matrix"
    purpose = "Turns meeting transcripts, recordings or call notes into minutes, decisions and owned action items."
    stage = StageEnum.MOM
    required_inputs = ["normalized_text"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        transcript = input_data.get("transcript") or input_data.get("normalized_input") or input_data.get("text") or ""
        if not transcript.strip():
            raise ValueError("Input text cannot be empty for the MOM Agent.")

        logger.info(f"[MomAgent] Executing MOM Agent on transcript length {len(transcript)}...")

        # No fallback: minutes must come from the transcript, never from a sample meeting.
        raw_mom = await generate_mom(transcript, api_key=api_key)

        def text(value) -> Optional[str]:
            value = str(value).strip() if value is not None else ""
            return value if value and value.lower() not in ("null", "none", "n/a") else None

        def as_list(key: str) -> List[Any]:
            value = raw_mom.get(key)
            return value if isinstance(value, list) else []

        decisions = []
        for idx, d in enumerate(as_list("decisions_finalized") or as_list("decisions")):
            d = d if isinstance(d, dict) else {"decision": d}
            decisions.append({
                "decision_id": f"DEC-{idx + 1:03d}",
                "decision": text(d.get("decision") or d.get("text")) or str(d),
                "speaker": text(d.get("speaker")),
                "context": text(d.get("context")),
            })

        actions = []
        for idx, a in enumerate(as_list("action_items")):
            a = a if isinstance(a, dict) else {"action": a}
            actions.append({
                "action_id": f"ACT-{idx + 1:03d}",
                "action": text(a.get("action") or a.get("description")) or str(a),
                "assignee": text(a.get("assignee") or a.get("owner")),
                "due_date": text(a.get("due_date")),
                "speaker": text(a.get("speaker")),
                "status": "Open",
            })

        return {
            "summary": text(raw_mom.get("discussion_summary") or raw_mom.get("summary")) or "",
            "attendees": [p if isinstance(p, dict) else {"name": str(p), "role": None} for p in as_list("attendees")],
            "key_points": as_list("key_points"),
            "requirements_identified": as_list("requirements_identified"),
            "decisions_finalized": decisions,
            "action_items": actions,
            "open_questions": as_list("open_questions"),
        }


mom_agent = MomAgent()
