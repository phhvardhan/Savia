from fastapi import APIRouter, HTTPException
from app.agents import AGENTS, AGENT_MAP
from app.orchestration import temporal_client
from app.orchestration.workflow_engine import workflow_engine
from app.orchestration.workflows import RunAgentRequest, SdlcWorkflow
from app.schemas.agent_schema import AgentRunRequest, AgentRunResponse

router = APIRouter()


@router.get("", tags=["SDLC Agents"])
async def list_agents():
    """Every registered agent with what it does, for the UI and manual testing."""
    return [
        {"id": a.id, "name": a.name, "purpose": a.purpose, "stage": a.stage.value, "required_inputs": a.required_inputs}
        for a in AGENTS
    ]


@router.post("/{agent_id}", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_agent(agent_id: str, payload: AgentRunRequest):
    if agent_id not in AGENT_MAP:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Known agents: {', '.join(AGENT_MAP)}.")

    workflow_id = payload.workflow_id
    if workflow_id and not workflow_engine.get_workflow(workflow_id):
        workflow_id = None  # unknown id: start a fresh session, as before
    input_text = (payload.input_text or "").strip()
    if not workflow_id:
        if not input_text:
            raise HTTPException(status_code=400, detail="Either workflow_id or input_text must be provided.")
        session = await temporal_client.start_session(f"Session for {agent_id}", [], input_text, "unknown")
        workflow_id = session.workflow_id

    # payload.api_key is not forwarded: it would be written into Temporal's workflow history.
    artifact = await temporal_client.update(workflow_id, SdlcWorkflow.run_agent_step, RunAgentRequest(
        agent_id=agent_id,
        input_text=input_text,
        document_type=payload.document_type or "functional_design",
        bypass_approval=bool(payload.bypass_approval),
    ))
    return AgentRunResponse(
        workflow_id=workflow_id,
        artifact_id=artifact.artifact_id,
        agent_name=agent_id,
        stage=artifact.stage.value,
        version=artifact.version,
        content=artifact.content,
    )
