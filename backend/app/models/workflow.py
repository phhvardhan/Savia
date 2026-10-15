from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class StageEnum(str, Enum):
    INGESTION = "ingestion"
    REQUIREMENTS = "requirements"
    MOM = "mom"
    USER_STORY = "user_story"
    DDL3 = "ddl3"
    TESTING = "testing"
    COMPLETED = "completed"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class TraceabilityLink(BaseModel):
    requirement_id: Optional[str] = None
    user_story_id: Optional[str] = None
    design_id: Optional[str] = None
    test_case_id: Optional[str] = None
    source_reference: Optional[str] = None


class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:8]}")
    workflow_id: str
    agent_name: str
    stage: StageEnum
    version: int = 1
    content: Dict[str, Any]
    traceability: TraceabilityLink = Field(default_factory=TraceabilityLink)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class WorkflowSession(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    title: str = "SAVIA SDLC Session"
    status: str = "in_progress"
    current_stage: StageEnum = StageEnum.INGESTION
    source_documents: List[Dict[str, Any]] = Field(default_factory=list)
    normalized_input: str = ""
    input_type: str = "unknown"
    outputs: Dict[str, Any] = Field(default_factory=lambda: {
        "mom": None,
        "agile_stories": None,
        "ddl3": None,
        "tests": None
    })
    approvals: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
