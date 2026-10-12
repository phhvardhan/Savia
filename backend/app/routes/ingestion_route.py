import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.services.document_parser import document_parser
from app.orchestration.workflow_engine import workflow_engine
from app.schemas.workflow_schema import WorkflowCreateRequest

router = APIRouter()


@router.post("/upload", tags=["Ingestion"])
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file filename provided.")

    temp_path = os.path.join(tempfile.gettempdir(), f"upload_{file.filename}")
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        normalized_text, input_type, metadata = await document_parser.parse_and_normalize(temp_path, file.filename)
        
        session = workflow_engine.create_workflow(
            title=f"Workflow - {file.filename}",
            source_documents=[metadata],
            normalized_input=normalized_text,
            input_type=input_type
        )

        return {
            "workflow_id": session.workflow_id,
            "filename": file.filename,
            "input_type": input_type,
            "metadata": metadata,
            "normalized_text_snippet": normalized_text[:500],
            "full_normalized_text": normalized_text,
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.post("/transcribe", tags=["Ingestion"])
async def transcribe_media(file: UploadFile = File(...)):
    return await upload_document(file=file)


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
