from typing import Optional, Dict, Any, List
from pydantic import BaseModel


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
    plan: List[Dict[str, Any]] = []
    source: str = "keyword"


class ApproveStageRequest(BaseModel):
    artifact_id: Optional[str] = None
    user_id: Optional[str] = None
    comments: Optional[str] = None
    decision: str = "approved"


class AdvanceStageRequest(BaseModel):
    target_stage: str
