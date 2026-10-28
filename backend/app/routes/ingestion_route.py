import os
import tempfile
from typing import List, Optional, Tuple
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from starlette.concurrency import run_in_threadpool
from app.core.extract import transcribe_audio_video
from app.services.document_parser import document_parser
from app.orchestration import temporal_client
from app.schemas.workflow_schema import WorkflowCreateRequest

router = APIRouter()


MAX_FILES = 10  # ponytail: fixed cap; raise with care, every file is parsed (and audio transcribed) inline


async def _parse_upload(upload: UploadFile) -> Tuple[str, str, dict]:
    """Parse one uploaded file via a uniquely named temp copy (two files may share a name)."""
    suffix = os.path.splitext(upload.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await upload.read())
        temp_path = tmp.name
    try:
        return await document_parser.parse_and_normalize(temp_path, upload.filename)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@router.post("/upload", tags=["Ingestion"])
async def upload_document(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),  # single-file clients keep working
):
    uploads = [f for f in (files or []) + ([file] if file else []) if f and f.filename]
    if not uploads:
        raise HTTPException(status_code=400, detail="No file provided.")
    if len(uploads) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Upload at most {MAX_FILES} files at a time.")

    parsed = []
    for upload in uploads:
        try:
            parsed.append(await _parse_upload(upload))
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not read '{upload.filename}': {e}")

    if len(parsed) == 1:
        normalized_text, input_type, metadata = parsed[0]
        source_documents = [metadata]
    else:
        # One header per file so agents and the recommender can tell files apart
        # (and fit_text can give each a fair share of the context window).
        total = len(parsed)
        normalized_text = "\n\n".join(
            f"===== FILE {i} of {total}: {meta['filename']} ({kind}) =====\n{text}"
            for i, (text, kind, meta) in enumerate(parsed, start=1)
        )
        kinds = {kind for _, kind, _ in parsed}
        input_type = kinds.pop() if len(kinds) == 1 else "mixed"
        source_documents = [meta for _, _, meta in parsed]
        metadata = {
            "filename": ", ".join(m["filename"] for m in source_documents),
            "input_type": input_type,
            "file_size_bytes": sum(m["file_size_bytes"] for m in source_documents),
            "character_count": len(normalized_text),
            "word_count": sum(m["word_count"] for m in source_documents),
            "file_count": total,
            "files": source_documents,
        }

    first = uploads[0].filename
    session = await temporal_client.start_session(
        title=f"Workflow - {first}" + (f" + {len(uploads) - 1} more" if len(uploads) > 1 else ""),
        source_documents=source_documents,
        normalized_input=normalized_text,
        input_type=input_type,
    )

    return {
        "workflow_id": session.workflow_id,
        "filename": metadata["filename"],
        "input_type": input_type,
        "metadata": metadata,
        "normalized_text_snippet": normalized_text[:500],
        "full_normalized_text": normalized_text,
    }


@router.post("/dictate", tags=["Ingestion"])
async def dictate(files: List[UploadFile] = File(...)):
    """Transcribe a short mic clip with the local Whisper model. No workflow is created."""
    upload = files[0]
    suffix = os.path.splitext(upload.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await upload.read())
    try:
        text = await run_in_threadpool(transcribe_audio_video, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not transcribe the recording: {e}")
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass
    # transcribe_audio_video returns "[Transcription: ...]" placeholders instead of raising
    return {"text": "" if text.startswith("[Transcription:") else text.strip()}


@router.post("/transcribe", tags=["Ingestion"])
async def transcribe_media(file: UploadFile = File(...)):
    return await upload_document(files=None, file=file)


@router.post("/analyze", tags=["Requirement Understanding"])
async def analyze_understanding(payload: dict):
    text = payload.get("text") or payload.get("normalized_text") or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    word_count = len(text.split())
    has_audio_transcript = "speaker" in text.lower() or "transcript" in text.lower()
    
    return {
        "character_count": len(text),
        "word_count": word_count,
        "is_audio_transcript": has_audio_transcript,
        "detected_entities": {
            "has_action_items": "action" in text.lower(),
            "has_user_stories": "user story" in text.lower() or "as a" in text.lower(),
            "has_design_specs": "design" in text.lower() or "architecture" in text.lower(),
            "has_test_cases": "test" in text.lower(),
        },
        "summary_snippet": text[:300]
    }
