from datetime import datetime, timezone
from app.core.extract import extract_text_from_file
from app.schemas.entities.meeting_entity import MeetingStatus


def process_meeting_text_only(
    meeting_id: str,
    file_path: str,
    meeting_repo,
):

    meeting_repo.update(meeting_id, {"status": MeetingStatus.PROCESSING})

    try:
        extracted_text = extract_text_from_file(file_path)

        meeting_repo.update(meeting_id, {
            "raw_text": extracted_text,
            "transcribed_at": datetime.now(timezone.utc).isoformat(),
        })

        try:
            import asyncio
            from app.services.minutes_service import MinutesService
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(MinutesService()._ensure_mom_generated(meeting_id))
            loop.close()
        except Exception:
            pass

        meeting_repo.update(meeting_id, {
            "status": MeetingStatus.COMPLETED,
        })

    except Exception as e:
        meeting_repo.update(meeting_id, {
            "status": MeetingStatus.FAILED,
        })
        raise