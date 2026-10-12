from fastapi import BackgroundTasks
from app.services.meeting_service import create_and_process_meeting
from app.schemas.entities.meeting_entity import MeetingSourceType
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends

class MeetingController:
    def __init__(self, meeting_repo, run_repo, run_step_repo, transcript_repo):
        self.meeting_repo = meeting_repo
        self.run_repo = run_repo
        self.run_step_repo = run_step_repo
        self.transcript_repo = transcript_repo

    async def upload_meeting(
        self,
        workspace_id: str,
        title: str,
        source_type: MeetingSourceType,
        uploaded_by: str,
        background_tasks: BackgroundTasks,
        file_bytes: bytes | None = None,
        original_filename: str | None = None,
        text: str | None = None,
    ):
        return create_and_process_meeting(
            workspace_id=workspace_id,
            title=title,
            source_type=source_type,
            uploaded_by=uploaded_by,
            background_tasks=background_tasks,
            meeting_repo=self.meeting_repo,
            run_repo=self.run_repo,
            run_step_repo=self.run_step_repo,
            transcript_repo=self.transcript_repo,
            file_bytes=file_bytes,
            original_filename=original_filename,
            text=text,
        )

    async def get_meeting(self, meeting_id: str):
        meeting = self.meeting_repo.get(meeting_id)
        if not meeting:
            return None
        return meeting

    async def get_transcript(self, meeting_id: str):
        return self.transcript_repo.list(filter_fn=lambda r: r.meeting_id == meeting_id)