from enum import Enum
from typing import List, Optional
from ..common_entity import BaseEntity


class RunType(str, Enum):
    TRANSCRIBE_AND_SUMMARIZE = "transcribe_and_summarize"
    JIRA_STORIES = "jira_stories"
    BRD_GENERATION = "brd_generation"
    DOCUMENT_SCORING = "document_scoring"
class RunStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
class RunStepStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
class RunStep(BaseEntity):
    run_id: str
    order: int
    name: str                            # "Transcribing audio", "Drafting summary and decisions"
    status: RunStepStatus = RunStepStatus.IDLE
    progress_percent: int = 0        
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
class Run(BaseEntity):
    type: RunType
    workspace_id: str
    source_type: str                 
    source_id: str                   
    template_id: Optional[str] = None   
    status: RunStatus = RunStatus.IDLE
    overall_progress_percent: int = 0
    current_step_name: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_by: str                      # user_id
    steps: List[str] = []                # list of RunStep ids, in order