



# POST   /runs                            # body: {type: transcribe|summarize|jira_stories|brd, source_id, template_id?}
# GET    /runs/{id}                       # status, progress %, elapsed, current step
# GET    /runs/{id}/steps                 # ordered step list w/ status each
# POST   /runs/{id}/cancel
# POST   /runs/{id}/notify-when-ready     # registers notification callback
# WS     /runs/{id}/stream                # websocket for live progress (polling fallback: GET /runs/{id})

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.controllers.run_controller import RunController
from app.schemas.entities.run_entity import Run, RunStep

router = APIRouter()
run_controller = RunController()


@router.get("/{run_id}", response_model=Run)
def get_run(run_id: str, current_user=Depends(get_current_user)):
    return run_controller.get_run(run_id)


@router.get("/{run_id}/steps", response_model=list[RunStep])
def get_steps(run_id: str, current_user=Depends(get_current_user)):
    return run_controller.get_steps(run_id)


@router.post("/{run_id}/cancel", response_model=Run)
def cancel_run(run_id: str, current_user=Depends(get_current_user)):
    return run_controller.cancel_run(run_id)

# NOTE: WS /runs/{id}/stream (live progress) intentionally not implemented
# yet — polling GET /runs/{id} works today; swap in a websocket once a
# real background worker exists to push updates instead of polling.
