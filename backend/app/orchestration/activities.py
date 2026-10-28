from typing import Any, Dict, Optional
from pydantic import BaseModel
from temporalio import activity
from temporalio.exceptions import ApplicationError
from app.agents import AGENT_MAP
from app.models.workflow import Artifact, WorkflowSession
from app.orchestration.orchestrator import savia_orchestrator
from app.orchestration.workflow_engine import workflow_engine


class RecommendInput(BaseModel):
    session: WorkflowSession
    raw_text: Optional[str] = None
    input_type: Optional[str] = None
    filename: Optional[str] = None


class PersistInput(BaseModel):
    session: WorkflowSession
    artifact: Optional[Artifact] = None


@activity.defn
async def recommend(args: RecommendInput) -> Dict[str, Any]:
    return await savia_orchestrator.recommend(args.session, args.raw_text, args.input_type, args.filename)


@activity.defn
async def run_agent(agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Agents signal bad input with ValueError; retrying that would never help.
    try:
        return await AGENT_MAP[agent_id].run(input_data)
    except ValueError as e:
        raise ApplicationError(str(e), type="ValueError", non_retryable=True) from e


@activity.defn
async def persist(args: PersistInput) -> None:
    """Writes the workflow's state to the JSON read model the API serves from."""
    workflow_engine.put_session(args.session)
    if args.artifact:
        workflow_engine.put_artifact(args.artifact)
