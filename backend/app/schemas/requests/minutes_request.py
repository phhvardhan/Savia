
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.entities.minutes_entity import ActionItemPriority, ActionItemStatus


class ActionItemCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    owner_user_id: Optional[str] = None
    owner_display_name: Optional[str] = None
    due_date: Optional[str] = None
    priority: ActionItemPriority = ActionItemPriority.MEDIUM
    status: ActionItemStatus = ActionItemStatus.UNASSIGNED


class ActionItemUpdateRequest(BaseModel):
    """Every field optional — this is a PATCH, client sends only what changed."""
    text: Optional[str] = Field(default=None, min_length=1, max_length=500)
    owner_user_id: Optional[str] = None
    owner_display_name: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[ActionItemPriority] = None
    status: Optional[ActionItemStatus] = None


class DecisionCreateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    made_by: Optional[str] = "Team"


class DecisionUpdateRequest(BaseModel):
    text: Optional[str] = None
    made_by: Optional[str] = None


class ApproveMinutesRequest(BaseModel):
    confirm: bool = Field(..., description="Client must explicitly confirm approval")


class SummaryUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)