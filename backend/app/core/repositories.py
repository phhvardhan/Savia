
from app.core.storage import FileRepository, EntityName
from app.schemas.entities.auth_entity import LocalUserProfile
from app.schemas.entities.workspace_entity  import Workspace, WorkspaceMember
from app.schemas.entities.meeting_entity  import Meeting
from app.schemas.entities.run_entity  import Run, RunStep

from app.schemas.entities.minutes_entity  import (TranscriptSegment,MeetingSummary,Decision,ActionItem)
from app.schemas.entities.jira_agent_entity  import Story
from app.schemas.entities.document_entity  import ( Document,DocumentSection,DocumentSource, DocumentVersionSnapshot,DocumentGap)
from app.schemas.entities.template_entity  import Template, TemplateSectionDef
from app.schemas.entities.notification_entity  import Notification


user_repo = FileRepository(LocalUserProfile, EntityName.USERS)
workspace_repo = FileRepository(Workspace, EntityName.WORKSPACES)
workspace_member_repo = FileRepository(WorkspaceMember, EntityName.WORKSPACE_MEMBERS)

meeting_repo = FileRepository(Meeting, EntityName.MEETINGS)

run_repo = FileRepository(Run, EntityName.RUNS)
run_step_repo = FileRepository(RunStep, EntityName.RUN_STEPS)


transcript_repo = FileRepository(TranscriptSegment, EntityName.TRANSCRIPTS)
summary_repo = FileRepository(MeetingSummary, EntityName.SUMMARIES)
decision_repo = FileRepository(Decision, EntityName.DECISIONS)
action_item_repo = FileRepository(ActionItem, EntityName.ACTION_ITEMS)

story_repo = FileRepository(Story, EntityName.STORIES)

document_repo = FileRepository(Document, EntityName.DOCUMENTS)
document_section_repo = FileRepository(DocumentSection, EntityName.DOCUMENT_SECTIONS)
document_source_repo = FileRepository(DocumentSource, EntityName.DOCUMENT_SOURCES)
document_version_repo = FileRepository(DocumentVersionSnapshot, EntityName.DOCUMENT_VERSIONS)
document_gap_repo = FileRepository(DocumentGap, EntityName.DOCUMENT_GAPS)

template_repo = FileRepository(Template, EntityName.TEMPLATES)
template_section_repo = FileRepository(TemplateSectionDef, EntityName.TEMPLATE_SECTIONS)

notification_repo = FileRepository(Notification, EntityName.NOTIFICATIONS)
from app.schemas.entities.minutes_entity import ClarificationQuestion
question_repo = FileRepository(ClarificationQuestion, EntityName.QUESTIONS)

from app.schemas.entities.document_entity import DocumentReview
review_repo = FileRepository(DocumentReview, EntityName.REVIEWS)