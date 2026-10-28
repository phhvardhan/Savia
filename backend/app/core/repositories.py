from app.core.storage import FileRepository, EntityName
from app.schemas.entities.auth_entity import LocalUserProfile
from app.schemas.entities.meeting_entity import Meeting
from app.schemas.entities.run_entity import Run, RunStep
from app.schemas.entities.minutes_entity import TranscriptSegment, MeetingSummary, Decision, ActionItem
from app.schemas.entities.jira_agent_entity import Story

user_repo = FileRepository(LocalUserProfile, EntityName.USERS)
meeting_repo = FileRepository(Meeting, EntityName.MEETINGS)
run_repo = FileRepository(Run, EntityName.RUNS)
run_step_repo = FileRepository(RunStep, EntityName.RUN_STEPS)
transcript_repo = FileRepository(TranscriptSegment, EntityName.TRANSCRIPTS)
summary_repo = FileRepository(MeetingSummary, EntityName.SUMMARIES)
decision_repo = FileRepository(Decision, EntityName.DECISIONS)
action_item_repo = FileRepository(ActionItem, EntityName.ACTION_ITEMS)
story_repo = FileRepository(Story, EntityName.STORIES)
