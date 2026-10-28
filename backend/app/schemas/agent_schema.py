from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    workflow_id: Optional[str] = None
    input_text: Optional[str] = None
    document_type: Optional[str] = "functional_design"
    use_case: Optional[str] = None
    rubric: Optional[str] = None
    # Hand-off: the generated output this run takes as its input, so the server builds the input from it.
    source_artifact_id: Optional[str] = None


class AgentRunResponse(BaseModel):
    workflow_id: Optional[str] = None
    artifact_id: str
    agent_name: str
    stage: str
    version: int
    content: Dict[str, Any]
    quality: Dict[str, Any] = Field(default_factory=dict)
    approval_status: str = "pending"
    upstream_used: List[str] = Field(default_factory=list)
    upstream_unapproved: List[str] = Field(default_factory=list)
    readiness: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None


class AgentRunStatus(BaseModel):
    id: str
    workflow_id: Optional[str] = None
    agent_id: str
    status: str
    artifact_id: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[AgentRunResponse] = None
