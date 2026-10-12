from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    workflow_id: Optional[str] = None
    input_text: Optional[str] = None
    document_type: Optional[str] = "functional_design"
    bypass_approval: Optional[bool] = False
    api_key: Optional[str] = None


class AgentRunResponse(BaseModel):
    workflow_id: Optional[str] = None
    artifact_id: str
    agent_name: str
    stage: str
    version: int
    content: Dict[str, Any]
