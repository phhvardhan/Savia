
from app.services.jira_agent_service import JiraAgentService
from app.schemas.requests.jira_agent_request import JiraAgentRunRequest, StoryUpdateRequest, PushToJiraRequest

jira_agent_service = JiraAgentService()
from app.utils.response import success_response, error_response



class JiraAgentController:

    async def start_run(self, payload: JiraAgentRunRequest, user):
        return await jira_agent_service.start_run(payload, user)

    def get_stories(self, jira_run_id: str):
        return jira_agent_service.get_stories(jira_run_id)

    def get_criteria(self, jira_run_id: str):
        return jira_agent_service.get_criteria(jira_run_id)

    def get_dependencies(self, jira_run_id: str):
        return jira_agent_service.get_dependencies(jira_run_id)

    def get_assumptions(self, jira_run_id: str):
        return jira_agent_service.get_assumptions(jira_run_id)

    def update_story(self, story_id: str, payload: StoryUpdateRequest):
        return jira_agent_service.update_story(story_id, payload)

    def approve_run(self, jira_run_id: str):
        return jira_agent_service.approve_run(jira_run_id)

    def push_to_jira(self, payload: PushToJiraRequest):
        return jira_agent_service.push_to_jira(payload)
