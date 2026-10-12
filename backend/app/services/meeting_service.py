import os
import uuid
from datetime import datetime, timezone
from fastapi import BackgroundTasks

from app.schemas.entities.meeting_entity import Meeting, MeetingSourceType, MeetingStatus
from app.schemas.entities.run_entity import Run, RunStep, RunType, RunStatus, RunStepStatus
from app.core.file_storage.factory import get_storage_service
from app.services.meeting_pipeline_service import process_meeting_diarization
from app.services.meeting_text_service import process_meeting_text_only


def create_and_process_meeting(
    workspace_id: str,
    title: str,
    source_type: MeetingSourceType,
    uploaded_by: str,
    background_tasks: BackgroundTasks,
    meeting_repo,
    run_repo,
    run_step_repo,
    transcript_repo,
    file_bytes: bytes | None = None,
    original_filename: str | None = None,
    text: str | None = None,
) -> Meeting:
    meeting_id = str(uuid.uuid4())

    if source_type == MeetingSourceType.TEXT:
        meeting = Meeting(            id=meeting_id,
            workspace_id=workspace_id,
            title=title,
            source_type=source_type,
            raw_text=text,
            status=MeetingStatus.COMPLETED,
            uploaded_by=uploaded_by,
        )
        meeting_repo.add(meeting)
        return meeting

   
    storage = get_storage_service()
    ext = "." + original_filename.rsplit(".", 1)[-1].lower()
    saved_filename = f"{meeting_id}{ext}"
    storage_path = storage.save(file_bytes, saved_filename)

    meeting = Meeting(
        id=meeting_id,
        workspace_id=workspace_id,
        title=title,
        source_type=source_type,
        source_filename=original_filename,
        storage_path=storage_path,
        status=MeetingStatus.UPLOADED,
        uploaded_by=uploaded_by,
    )
    meeting_repo.add(meeting)


    if source_type in (MeetingSourceType.VIDEO, MeetingSourceType.AUDIO):
        run_step_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())

        run_step = RunStep(
            id=run_step_id,
            run_id=run_id,
            order=0,
            name="Diarizing speakers and transcribing",
            status=RunStepStatus.IDLE,
            progress_percent=0,
        )
        run = Run(
            id=run_id,
            type=RunType.TRANSCRIBE_AND_SUMMARIZE,
            workspace_id=workspace_id,
            source_type=source_type,
            source_id=meeting_id,
            status=RunStatus.IDLE,
            overall_progress_percent=0,
            created_by=uploaded_by,
            steps=[run_step_id],
        )

        run_repo.add(run)
        run_step_repo.add(run_step)
        meeting_repo.update(meeting_id, {"active_run_id": run_id})

        background_tasks.add_task(
            process_meeting_diarization,
            meeting_id,
            storage_path,
            run_step_id,
            run_step_repo,
            transcript_repo,
            meeting_repo,
        )


    elif source_type == MeetingSourceType.FILE:
        background_tasks.add_task(
            process_meeting_text_only,
            meeting_id,
            storage_path,
            meeting_repo,
        )

    return meeting


def get_meeting_transcript(meeting_id: str, transcript_repo) -> list:
    return transcript_repo.list(filter_fn=lambda r: r.meeting_id == meeting_id)