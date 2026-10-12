from typing import Optional
from ..common_entity import BaseEntity
from enum import Enum

class MeetingSourceType(str, Enum):
    VIDEO = "video"  
    AUDIO = "audio" 
    TEXT = "text"   
    FILE = "file"   


class MeetingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    
class Meeting(BaseEntity):
    workspace_id: str
    title: str                     
    source_type: MeetingSourceType
    source_filename: Optional[str] = None   
    storage_path: Optional[str] = None     
    raw_text: Optional[str] = None

    duration_seconds: Optional[float] = None 
    detected_language: Optional[str] = None    
    transcribed_at: Optional[str] = None  
    participant_count: Optional[int] = None
    team: Optional[str] = None  
    category: Optional[str] = None     
    status: MeetingStatus = MeetingStatus.UPLOADED
    uploaded_by: str                
    approved_at: Optional[str] = None  
    approved_by: Optional[str] = None  
    active_run_id: Optional[str] = None


class TranscriptSegment(BaseEntity):
    meeting_id: str
    speaker_name: str
    start_seconds: float
    end_seconds: float
    text: str