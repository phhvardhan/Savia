from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WorkflowCreateRequest(BaseModel):
    title: Optional[str] = "SAVIA SDLC Session"
    normalized_input: Optional[str] = ""
    input_type: Optional[str] = "unknown"
    source_documents: Optional[List[Dict[str, Any]]] = []


class RecommendationRequest(BaseModel):
    workflow_id: Optional[str] = None
    raw_text: Optional[str] = None
    input_type: Optional[str] = None
    filename: Optional[str] = None


class RecommendationResponse(BaseModel):
    workflow_id: Optional[str] = None
    input_type: str
    current_stage: str
    recommended_agents: List[Dict[str, Any]]
    primary_agent: str
    primary_reason: str
    missing_information: List[str]
    next_action: str


class ApproveStageRequest(BaseModel):
    user_id: Optional[str] = "system_user"
    comments: Optional[str] = "Approved"


class AdvanceStageRequest(BaseModel):
    target_stage: str
    bypass_approval: Optional[bool] = False
