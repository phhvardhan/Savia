from fastapi import APIRouter, HTTPException, status
from app.orchestration.orchestrator import savia_orchestrator
from app.orchestration.workflow_engine import workflow_engine
from app.schemas.workflow_schema import RecommendationRequest, RecommendationResponse
from app.models.workflow import WorkflowSession

router = APIRouter()


@router.post("/recommend", response_model=RecommendationResponse, tags=["SAVIA Layer / SAVIA Recommendation"])
async def savia_recommend_agent(payload: RecommendationRequest):
    """
    SAVIA Recommendation Layer:
    Analyzes raw user input (text, PDF snippet, transcript, or document content) and current SDLC stage
    to recommend the optimal downstream modular agent (MOM, Agile User Story, DDL3, or Test Agent).
    """
    session = None
    if payload.workflow_id:
        session = workflow_engine.get_workflow(payload.workflow_id)

    raw_text = payload.raw_text or (session.normalized_input if session else "")
    input_type = payload.input_type or (session.input_type if session else "unknown")

    if not raw_text and not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either workflow_id or raw_text must be provided to SAVIA Recommendation Layer."
        )

    if not session:
        # Create temporary transient session for analysis
        session = WorkflowSession(
            normalized_input=raw_text,
            input_type=input_type
        )

    recommendation = savia_orchestrator.analyze_and_recommend(
        session=session,
        raw_text=raw_text,
        input_type=input_type,
        filename=payload.filename
    )

    return recommendation


@router.post("/orchestrate", tags=["SAVIA Layer / SAVIA Recommendation"])
async def savia_orchestrate(payload: dict):
    """
    High-level SAVIA orchestration entrypoint for analyzing and organizing complete workflow pipeline requests.
    """
    workflow_id = payload.get("workflow_id")
    session = workflow_engine.get_workflow(workflow_id) if workflow_id else None
    
    raw_text = payload.get("text") or (session.normalized_input if session else "")
    input_type = payload.get("input_type") or (session.input_type if session else "unknown")

    if not session:
        session = workflow_engine.create_workflow(
            title="SAVIA Orchestrated Pipeline",
            normalized_input=raw_text,
            input_type=input_type
        )

    rec = savia_orchestrator.analyze_and_recommend(session, raw_text, input_type)

    return {
        "workflow": session.dict(),
        "recommendation": rec,
        "status": "orchestrated"
    }
