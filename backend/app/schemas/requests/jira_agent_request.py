
from typing import List, Optional

from pydantic import BaseModel, Field


class JiraAgentRunRequest(BaseModel):
    meeting_id: Optional[str] = None
    context_name: Optional[str] = None
    notes: Optional[str] = None
    project: Optional[str] = "Digital Payments (DPX)"
    sprint: Optional[str] = "Sprint 25"
    team: Optional[str] = "Engineering & Product"
    options: Optional[List[str]] = None


class StoryUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5_000)
    acceptance_criteria: Optional[List[str]] = None
    priority: Optional[str] = None
    story_points: Optional[int] = Field(default=None, ge=0, le=100)


class PushToJiraRequest(BaseModel):
    story_ids: List[str] = Field(..., min_length=1)
    jira_url: Optional[str] = None
    email: Optional[str] = None
    api_token: Optional[str] = None
    project_key: Optional[str] = None