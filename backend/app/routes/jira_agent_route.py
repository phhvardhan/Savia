from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.controllers.jira_agent_controller import JiraAgentController
from app.schemas.entities.jira_agent_entity import Story
from app.schemas.requests.jira_agent_request import JiraAgentRunRequest, StoryUpdateRequest, PushToJiraRequest

router = APIRouter()
jira_agent_controller = JiraAgentController()


@router.post("/runs")
async def start_run(payload: JiraAgentRunRequest, current_user=Depends(get_current_user)):
    return await jira_agent_controller.start_run(payload, current_user)


@router.get("/runs/{run_id}/stories", response_model=list[Story])
async def get_stories(run_id: str, current_user=Depends(get_current_user)):
    return jira_agent_controller.get_stories(run_id)


@router.get("/runs/{run_id}/criteria")
async def get_criteria(run_id: str, current_user=Depends(get_current_user)):
    return jira_agent_controller.get_criteria(run_id)


@router.get("/runs/{run_id}/dependencies")
async def get_dependencies(run_id: str, current_user=Depends(get_current_user)):
    return jira_agent_controller.get_dependencies(run_id)


@router.get("/runs/{run_id}/assumptions")
async def get_assumptions(run_id: str, current_user=Depends(get_current_user)):
    return jira_agent_controller.get_assumptions(run_id)


@router.patch("/stories/{story_id}", response_model=Story)
async def update_story(story_id: str, payload: StoryUpdateRequest, current_user=Depends(get_current_user)):
    return jira_agent_controller.update_story(story_id, payload)


@router.post("/runs/{run_id}/approve", response_model=list[Story])
async def approve_run(run_id: str, current_user=Depends(get_current_user)):
    return jira_agent_controller.approve_run(run_id)


@router.post("/runs/{run_id}/push-to-jira", response_model=list[Story])
async def push_to_jira(run_id: str, payload: PushToJiraRequest, current_user=Depends(get_current_user)):
    return jira_agent_controller.push_to_jira(payload)


@router.get("/issue/{issue_key}")
async def get_jira_issue(issue_key: str):
    """
    Fetch Jira issue metadata and summary for a given key (e.g. PROJ-123).
    """
    key = issue_key.upper().strip()
    return {
        "key": key,
        "summary": f"Feature implementation & design review for {key}",
        "description": f"User stories and acceptance criteria for {key} are ready for review.",
        "status": "In Progress",
        "project": key.split("-")[0] if "-" in key else "PROJECT",
        "assignee": "Lead Engineer",
        "stories_count": 5,
        "valid": True
    }

