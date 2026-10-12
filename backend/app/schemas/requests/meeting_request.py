from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.entities.meeting_entity import MeetingSourceType, MeetingStatus


class MeetingUploadRequest(BaseModel):
    """
    Multipart form fields already validated by FastAPI (Form/File in the route).
    This model documents the shape for OpenAPI docs and any internal validation.
    """
    workspace_id: str
    title: str
    source_type: MeetingSourceType
    uploaded_by: str
    text: Optional[str] = Field(
        default=None,
        description="Required only when source_type is 'text'",
    )


class MeetingUploadResponse(BaseModel):
    meeting_id: str
    workspace_id: str
    title: str
    source_type: MeetingSourceType
    status: MeetingStatus
    active_run_id: Optional[str] = None
    message: str


class TranscriptSegmentResponse(BaseModel):
    speaker: str
    start_seconds: float
    end_seconds: float
    text: str


class MeetingTranscriptResponse(BaseModel):
    meeting_id: str
    segments: list[TranscriptSegmentResponse]