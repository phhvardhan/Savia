from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid

LEGACY_OUTPUT_KEYS = {"agile_stories": "agile-stories", "tests": "test"}


def _now() -> str:
    return datetime.utcnow().isoformat()


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
    requirement_ids: List[str] = Field(default_factory=list)
    user_story_ids: List[str] = Field(default_factory=list)
    design_ids: List[str] = Field(default_factory=list)
    test_case_ids: List[str] = Field(default_factory=list)
    upstream_artifact_ids: List[str] = Field(default_factory=list)
    source_reference: Optional[str] = None


class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:8]}")
    workflow_id: str
    agent_name: str
    stage: StageEnum
    version: int = 1
    content: Dict[str, Any]
    traceability: TraceabilityLink = Field(default_factory=TraceabilityLink)
    quality: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_now)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    approval_comments: Optional[str] = None

    @field_validator("traceability", mode="before")
    @classmethod
    def _legacy_traceability(cls, value):
        return value if isinstance(value, (dict, TraceabilityLink)) else {}


class WorkflowSession(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    title: str = "SAVIA SDLC Session"
    status: str = "in_progress"
    current_stage: StageEnum = StageEnum.INGESTION
    source_documents: List[Dict[str, Any]] = Field(default_factory=list)
    normalized_input: str = ""
    input_type: str = "unknown"
    outputs: Dict[str, Any] = Field(default_factory=dict)
    approvals: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)

    @field_validator("outputs", mode="before")
    @classmethod
    def _legacy_outputs(cls, value):
        if not isinstance(value, dict):
            return {}
        return {LEGACY_OUTPUT_KEYS.get(k, k): v for k, v in value.items() if v}

    def log(self, event: str, **details: Any) -> None:
        self.history.append({"timestamp": _now(), "event": event, **details})
