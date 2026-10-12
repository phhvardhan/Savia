
from enum import Enum
from typing import Optional
from ..common_entity import BaseEntity

class TranscriptSegment(BaseEntity):
    meeting_id: str
    speaker_name: str
    start_seconds: float
    end_seconds: float
    text: str
class MeetingSummary(BaseEntity):
    meeting_id: str
    content: str  
    generated_by_run_id: str
    key_points: Optional[list[str]] = None
    requirements_identified: Optional[list[str]] = None
    open_questions: Optional[list[str]] = None
class Decision(BaseEntity):
    meeting_id: str
    text: str
    made_by: Optional[str] = None  
    timestamp_seconds: Optional[float] = None  
class ActionItemPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
class ActionItemStatus(str, Enum):
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    DONE = "done"
class ActionItem(BaseEntity):
    meeting_id: str
    text: str
    owner_user_id: Optional[str] = None
    owner_display_name: Optional[str] = None 
    due_date: Optional[str] = None             # ISO date
    priority: ActionItemPriority = ActionItemPriority.MEDIUM
    status: ActionItemStatus = ActionItemStatus.UNASSIGNED
    timestamp_seconds: Optional[float] = None 
    is_manually_added: bool = False 
    suggested_by_ai: bool = True

class ClarificationQuestion(BaseEntity):
    meeting_id: str
    question: str
    answer: Optional[str] = None
    order: int = 0