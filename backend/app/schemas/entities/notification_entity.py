
from enum import Enum
from typing import Optional

from ..common_entity import BaseEntity


class NotificationType(str, Enum):
    RUN_COMPLETED = "run_completed"
    APPROVAL_NEEDED = "approval_needed"
    DOCUMENT_PUBLISHED = "document_published"
    MENTIONED = "mentioned"


class Notification(BaseEntity):
    user_id: str                      
    type: NotificationType
    title: str
    message: str
    related_entity_type: Optional[str] = None  
    related_entity_id: Optional[str] = None
    is_read: bool = False