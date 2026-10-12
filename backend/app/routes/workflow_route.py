from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.orchestration.workflow_engine import workflow_engine
from app.orchestration.stage_manager import stage_manager
from app.schemas.workflow_schema import (
    WorkflowCreateRequest, ApproveStageRequest, AdvanceStageRequest
)
from app.models.workflow import StageEnum, WorkflowSession, Artifact

router = APIRouter()


@router.post("", tags=["Workflows"])
async def create_workflow(payload: WorkflowCreateRequest):
    session = workflow_engine.create_workflow(
        title=payload.title or "SAVIA SDLC Session",
        source_documents=payload.source_documents or [],
        normalized_input=payload.normalized_input or "",
        input_type=payload.input_type or "unknown"
    )
    return session


@router.get("/{workflow_id}", tags=["Workflows"])
async def get_workflow(workflow_id: str):
    session = workflow_engine.get_workflow(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return session


@router.post("/{workflow_id}/approve", tags=["Workflows"])
async def approve_stage(workflow_id: str, payload: ApproveStageRequest):
    session = workflow_engine.get_workflow(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    updated_session = stage_manager.approve_stage(
        session=session,
        stage=session.current_stage,
        user_id=payload.user_id,
        comments=payload.comments
    )
    return {
        "status": "approved",
        "stage": session.current_stage.value,
        "workflow": updated_session
    }


@router.post("/{workflow_id}/advance", tags=["Workflows"])
async def advance_stage(workflow_id: str, payload: AdvanceStageRequest):
    session = workflow_engine.get_workflow(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    try:
        target_stage = StageEnum(payload.target_stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid target stage '{payload.target_stage}'. Valid stages: {[s.value for s in StageEnum]}")

    success, reason, updated = stage_manager.advance_stage(
        session=session,
        target_stage=target_stage,
        bypass_approval=payload.bypass_approval
    )

    if not success:
        raise HTTPException(status_code=400, detail=reason)

    return {
        "status": "advanced",
        "current_stage": updated.current_stage.value,
        "workflow": updated
    }


@router.get("/{workflow_id}/artifacts", tags=["Artifacts"])
async def list_workflow_artifacts(workflow_id: str):
    artifacts = workflow_engine.get_workflow_artifacts(workflow_id)
    return artifacts


@router.get("/artifacts/{artifact_id}", tags=["Artifacts"])
async def get_artifact(artifact_id: str):
    artifact = workflow_engine.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    return artifact
