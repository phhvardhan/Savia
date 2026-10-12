

from enum import Enum
from typing import List, Optional

from ..common_entity import BaseEntity


class StoryStatus(str, Enum):
    DRAFTING = "drafting"
    DRAFT = "draft"
    APPROVED = "approved"
    PUSHED = "pushed"          # successfully created in real Jira


class Story(BaseEntity):
    meeting_id: str                       # source minutes
    jira_run_id: str                      # which Run produced this draft
    title: str
    description: str
    acceptance_criteria: List[str] = []
    priority: str = "medium"
    story_points: Optional[int] = None
    sprint: Optional[str] = None          # "Sprint 25"
    team: Optional[str] = None
    dependencies: List[str] = []
    assumptions: List[str] = []
    status: StoryStatus = StoryStatus.DRAFTING
    jira_issue_key: Optional[str] = None  # e.g. "DPX-241", set after push
    jira_issue_url: Optional[str] = None  # direct link to ticket
    pushed_at: Optional[str] = None