import os
import tempfile

from app.core.extract import extract_audio_to_wav, transcribe_whisper_segments
from app.core.diarize import diarize_audio
from app.core.merge import merge_diarization_and_transcript
from app.schemas.entities.run_entity import RunStepStatus
from app.schemas.entities.meeting_entity import MeetingStatus, TranscriptSegment
from datetime import datetime, timezone


def process_meeting_diarization(
    meeting_id: str,
    file_path: str,         
    run_step_id: str,
    run_step_repo,
    transcript_repo,
    meeting_repo,
):
    run_step_repo.update(run_step_id, {
        "status": RunStepStatus.PROCESSING,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })
    meeting_repo.update(meeting_id, {"status": MeetingStatus.PROCESSING})

    temp_wav = os.path.join(tempfile.gettempdir(), f"{meeting_id}.wav")

    try:

        wav_path = extract_audio_to_wav(file_path, temp_wav)

        transcript_segments = transcribe_whisper_segments(wav_path)
        diarization_segments = diarize_audio(wav_path)  # HF_TOKEN missing ho to [] aayega

        merged = merge_diarization_and_transcript(diarization_segments, transcript_segments)

        full_text_parts = []
        for seg in merged:
            spk = seg.get("speaker_name") or seg.get("speaker") or "Speaker"
            st_sec = float(seg.get("start_seconds", seg.get("start", 0.0)))
            end_sec = float(seg.get("end_seconds", seg.get("end", 0.0)))
            txt = str(seg.get("text", "")).strip()
            if txt:
                transcript_repo.add(TranscriptSegment(
                    meeting_id=meeting_id,
                    speaker_name=spk,
                    start_seconds=st_sec,
                    end_seconds=end_sec,
                    text=txt,
                ))
                full_text_parts.append(txt)

        raw_text_full = " ".join(full_text_parts)
        meeting_repo.update(meeting_id, {
            "raw_text": raw_text_full,
            "transcribed_at": datetime.now(timezone.utc).isoformat(),
        })
        run_step_repo.update(run_step_id, {
            "progress_percent": 85,
        })

        # Pre-compute MoM summary, decisions, questions and action items before finishing
        try:
            import asyncio
            from app.services.minutes_service import MinutesService
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(MinutesService()._ensure_mom_generated(meeting_id))
            loop.close()
        except Exception as mom_e:
            pass

        meeting_repo.update(meeting_id, {
            "status": MeetingStatus.COMPLETED,
        })
        run_step_repo.update(run_step_id, {
            "status": RunStepStatus.COMPLETED,
            "progress_percent": 100,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as e:
        meeting_repo.update(meeting_id, {"status": MeetingStatus.FAILED})
        try:
            run_step_repo.update(run_step_id, {
                "status": RunStepStatus.FAILED,
            })
        except Exception:
            pass
        raise

    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)