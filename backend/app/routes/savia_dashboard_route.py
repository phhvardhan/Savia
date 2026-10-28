from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter

from app.agents import AGENT_MAP
from app.core.db import db
from app.orchestration.stage_manager import stage_manager
from app.orchestration.workflow_engine import workflow_engine

router = APIRouter()

STAGE_LABELS = {
    "ingestion": "Intake",
    "requirements": "Requirements",
    "mom": "Requirements",
    "user_story": "Requirements",
    "ddl3": "Design",
    "testing": "Testing",
    "completed": "Release",
}
IMAGES = ["/assets/ran1.jpg", "/assets/ran2.jpg", "/assets/ran3.jpg"]
ACCENTS = ["accentRed", "accentTagBlue", "accentTagGreen"]


def _times(count: int) -> str:
    return "Used once this week" if count == 1 else "Used twice this week" if count == 2 else f"Used {count} times this week"


@router.get("/dashboard", tags=["SAVIA Dashboard"])
async def get_dashboard_summary() -> Dict[str, Any]:
    workflows = workflow_engine.list_workflows()
    running = db.query("SELECT agent_id, workflow_id, started_at FROM runs WHERE status IN ('queued', 'running')")
    failed = db.query("SELECT COUNT(*) AS n FROM runs WHERE status = 'failed'")[0]["n"]
    waiting = [w for w in workflows if stage_manager.pending_artifacts(w)]

    counters = [
        {
            "id": "running",
            "value": str(len(running)),
            "label": "Running for you",
            "hint": f"Across {len({r['workflow_id'] for r in running})} workflows" if running else "Nothing running right now",
            "accent": "accentYellow",
        },
        {
            "id": "waiting",
            "value": str(len(waiting)),
            "label": "Waiting on your approval",
            "hint": f"{sum(len(stage_manager.pending_artifacts(w)) for w in waiting)} outputs to review" if waiting else "Nothing waiting",
            "accent": "accentMagenta",
        },
        {
            "id": "stale",
            "value": str(failed),
            "label": "Failed runs",
            "hint": "Open the workflow to retry" if failed else "No failed runs",
            "accent": "accentAmber",
        },
    ]

    runs = []
    for w in workflows[:5]:
        latest = workflow_engine.latest_artifacts(w.workflow_id)
        pending = [a for a in latest.values() if a.approval_status.value != "approved"]
        state = "Needs you" if pending else "Running" if w.status == "in_progress" else "Approved"
        runs.append({
            "id": w.workflow_id,
            "title": f"{STAGE_LABELS.get(w.current_stage.value, w.current_stage.value)} · {w.title}",
            "meta": w.status.replace("_", " ").capitalize(),
            "metricLabel": "Approved outputs",
            "metricValue": f"{len(latest) - len(pending)} of {len(latest)}",
            "state": state,
            "stateTone": "doneSoft" if state == "Approved" else "runningSoft",
            "accent": "accentOrange" if pending else "accentGreen" if w.status == "in_progress" else "accentBlue",
        })

    since = (datetime.utcnow() - timedelta(days=7)).isoformat()
    weekly = db.query(
        "SELECT agent_id, COUNT(*) AS n FROM runs WHERE status = 'done' AND finished_at >= ?"
        " GROUP BY agent_id ORDER BY n DESC LIMIT 3",
        (since,),
    )
    ran_this_week = [
        {
            "id": row["agent_id"],
            "title": AGENT_MAP[row["agent_id"]].name if row["agent_id"] in AGENT_MAP else row["agent_id"],
            "text": AGENT_MAP[row["agent_id"]].purpose if row["agent_id"] in AGENT_MAP else "",
            "stage": STAGE_LABELS.get(AGENT_MAP[row["agent_id"]].stage.value, "") if row["agent_id"] in AGENT_MAP else "",
            "stageHref": None,
            "usage": _times(row["n"]),
            "image": IMAGES[i % len(IMAGES)],
            "accent": ACCENTS[i % len(ACCENTS)],
        }
        for i, row in enumerate(weekly)
    ]

    return {"counters": counters, "runs": runs, "ran_this_week": ran_this_week, "total_workflows": len(workflows)}
