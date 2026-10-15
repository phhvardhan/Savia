from fastapi import APIRouter, HTTPException, status
from app.agents import AGENTS, AGENT_MAP
from app.orchestration.workflow_engine import workflow_engine
from app.orchestration.stage_manager import stage_manager
from app.models.workflow import StageEnum, TraceabilityLink
from app.schemas.agent_schema import AgentRunRequest, AgentRunResponse

router = APIRouter()


async def _run_agent_pipeline(agent_name: str, stage_enum: StageEnum, payload: AgentRunRequest) -> AgentRunResponse:
    agent = AGENT_MAP.get(agent_name)
    if not agent:
        raise HTTPException(status_code=400, detail=f"Agent '{agent_name}' not found.")

    session = None
    input_text = payload.input_text or ""

    if payload.workflow_id:
        session = workflow_engine.get_workflow(payload.workflow_id)
        if session:
            if not input_text:
                input_text = session.normalized_input

            # Check approval gate if not bypassed
            allowed, reason = stage_manager.can_advance(session, stage_enum, bypass_approval=payload.bypass_approval)
            if not allowed:
                raise HTTPException(status_code=400, detail=reason)

    if not input_text and not session:
        raise HTTPException(status_code=400, detail="Either workflow_id or input_text must be provided.")

    if not session:
        session = workflow_engine.create_workflow(
            title=f"Session for {agent_name}",
            normalized_input=input_text
        )

    # Prepare input payload for agent
    input_data = {
        "text": input_text,
        "normalized_input": input_text,
        "document_type": payload.document_type or "functional_design",
        "mom": session.outputs.get("mom"),
        "agile_stories": session.outputs.get("agile_stories"),
        "ddl3": session.outputs.get("ddl3"),
        "outputs": session.outputs,
    }

    # Execute agent
    try:
        content = await agent.run(input_data, api_key=payload.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent '{agent_name}' execution failed: {str(e)}")

    # Build traceability link
    traceability = TraceabilityLink(
        requirement_id=session.workflow_id,
        user_story_id="US-001" if stage_enum != StageEnum.MOM else None,
        design_id="DES-001" if stage_enum in [StageEnum.DDL3, StageEnum.TESTING] else None,
        test_case_id="TC-001" if stage_enum == StageEnum.TESTING else None,
        source_reference=session.workflow_id
    )

    # Save artifact & update session stage
    artifact = workflow_engine.save_artifact(
        workflow_id=session.workflow_id,
        agent_name=agent_name,
        stage=stage_enum,
        content=content,
        traceability=traceability
    )

    # Automatically update session stage if applicable
    stage_manager.advance_stage(session, stage_enum, bypass_approval=True)

    return AgentRunResponse(
        workflow_id=session.workflow_id,
        artifact_id=artifact.artifact_id,
        agent_name=agent_name,
        stage=stage_enum.value,
        version=artifact.version,
        content=content
    )


@router.get("", tags=["SDLC Agents"])
async def list_agents():
    """Every registered agent with what it does, for the UI and manual testing."""
    return [
        {"id": a.id, "name": a.name, "purpose": a.purpose, "stage": a.stage.value, "required_inputs": a.required_inputs}
        for a in AGENTS
    ]


@router.post("/{agent_id}", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_agent(agent_id: str, payload: AgentRunRequest):
    agent = AGENT_MAP.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Known agents: {', '.join(AGENT_MAP)}.")
    return await _run_agent_pipeline(agent_id, agent.stage, payload)
