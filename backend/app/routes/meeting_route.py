from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from typing import Optional

from app.schemas.entities.meeting_entity import MeetingSourceType
from app.controllers.meeting_controller import MeetingController
from app.core.repositories import FileRepository, EntityName
from app.schemas.entities.meeting_entity import Meeting, TranscriptSegment
from app.schemas.entities.run_entity import Run, RunStep

router = APIRouter(tags=["meetings"])


def get_meeting_controller() -> MeetingController:
    return MeetingController(
        meeting_repo=FileRepository(Meeting, EntityName.MEETINGS),
        run_repo=FileRepository(Run, EntityName.RUNS),
        run_step_repo=FileRepository(RunStep, EntityName.RUN_STEPS),
        transcript_repo=FileRepository(TranscriptSegment, EntityName.TRANSCRIPTS),
    )


@router.get("/", response_model=list[Meeting])
def list_all_meetings(controller: MeetingController = Depends(get_meeting_controller)):
    return controller.meeting_repo.list()


@router.post("/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    source_type: MeetingSourceType = Form(...),
    workspace_id: str = Form(...),
    title: str = Form(...),
    uploaded_by: str = Form(...),
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    controller: MeetingController = Depends(get_meeting_controller),
):
    if source_type == MeetingSourceType.TEXT:
        if not text or not text.strip():
            raise HTTPException(400, "text is required when source_type is 'text'")
        return await controller.upload_meeting(
            workspace_id=workspace_id,
            title=title,
            source_type=source_type,
            uploaded_by=uploaded_by,
            background_tasks=background_tasks,
            text=text,
        )

    if not file:
        raise HTTPException(400, f"file is required when source_type is '{source_type.value}'")

    file_bytes = await file.read()
    return await controller.upload_meeting(
        workspace_id=workspace_id,
        title=title,
        source_type=source_type,
        uploaded_by=uploaded_by,
        background_tasks=background_tasks,
        file_bytes=file_bytes,
        original_filename=file.filename,
    )


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str, controller: MeetingController = Depends(get_meeting_controller)):
    meeting = await controller.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


@router.get("/{meeting_id}/transcript")
async def get_transcript(meeting_id: str, controller: MeetingController = Depends(get_meeting_controller)):
    return await controller.get_transcript(meeting_id)