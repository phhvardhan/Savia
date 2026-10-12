from fastapi import APIRouter, HTTPException, status
from app.agents import AGENT_MAP
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
        "user_stories": session.outputs.get("user_stories"),
        "ddl3": session.outputs.get("ddl3"),
        "outputs": session.outputs,
    }

    # Execute agent
    try:
        content = await agent.run(input_data, api_key=payload.api_key)
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


@router.post("/mom", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_mom_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("mom", StageEnum.MOM, payload)


@router.post("/user-stories", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_user_stories_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("user-stories", StageEnum.USER_STORY, payload)


@router.post("/ddl3", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_ddl3_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("ddl3", StageEnum.DDL3, payload)


@router.post("/test", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_test_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("test", StageEnum.TESTING, payload)


@router.post("/readiness-scoring", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_readiness_scoring_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("readiness-scoring", StageEnum.COMPLETED, payload)


@router.post("/gap-analysis", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_gap_analysis_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("gap-analysis", StageEnum.REQUIREMENTS, payload)


@router.post("/change-impact", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_change_impact_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("change-impact", StageEnum.DDL3, payload)


@router.post("/kdd-package", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_kdd_package_agent(payload: AgentRunRequest):
    return await _run_agent_pipeline("kdd-package", StageEnum.DDL3, payload)
