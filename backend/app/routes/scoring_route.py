import os
import re
import tempfile
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request

from app.core.security import get_current_user
from app.controllers.scoring_controller import ScoringController
from app.schemas.requests.document_request import ApplyGapSuggestionRequest
from app.core.extract import extract_text_from_file

router = APIRouter()
scoring_controller = ScoringController()


@router.post("/evaluate")
async def evaluate_document(
    request: Request,
    file: Optional[UploadFile] = File(None),
    rubric: Optional[str] = Form("Enterprise SDLC Standard (ISO/IEC 25010 & GxP)"),
    dimensions: Optional[str] = Form(None),
    notes_text: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
):
    doc_name = "Uploaded Specification"
    content_text = ""

    # Check for multipart file upload
    if file:
        doc_name = file.filename or "Document"
        ext = os.path.splitext(doc_name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            content_text = extract_text_from_file(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    elif notes_text and notes_text.strip():
        content_text = notes_text.strip()
        doc_name = "Written Requirements"

    else:
        # Check if JSON body was sent
        try:
            body = await request.json()
            if body:
                content_text = body.get("document_text") or body.get("notes") or ""
                doc_name = body.get("document_name") or doc_name
                rubric = body.get("rubric") or rubric
                if "dimensions" in body:
                    dimensions = json.dumps(body.get("dimensions"))
        except Exception:
            pass

    # Ensure content_text is populated with actual specification if missing or sparse
    if not content_text or len(content_text.strip()) < 60:
        from app.core.repositories import (
            document_repo, document_section_repo, meeting_repo,
            summary_repo, decision_repo, action_item_repo, transcript_repo,
        )
        docs = document_repo.list()
        if docs:
            latest_doc = docs[-1]
            sections = document_section_repo.list(filter_fn=lambda s: s.document_id == latest_doc.id)
            if sections:
                clean_dt = re.sub(r'\bBRD\b\s*[-—–:]*\s*', '', latest_doc.title, flags=re.IGNORECASE).strip() or "Requirements Specification"
                content_text = f"SPECIFICATION: {clean_dt}\n\n" + "\n\n".join(f"### {s.title}\n{s.content}" for s in sections)
                if doc_name in ("Uploaded Specification", "Document", "Enterprise SDLC Specification"):
                    doc_name = clean_dt
        if not content_text or len(content_text.strip()) < 60:
            meetings = meeting_repo.list()
            if meetings:
                latest_m = meetings[-1]
                clean_mt = re.sub(r'\bBRD\b\s*[-—–:]*\s*', '', latest_m.title, flags=re.IGNORECASE).strip() or "Requirements Specification"
                summaries = summary_repo.list(filter_fn=lambda s: s.meeting_id == latest_m.id)
                decisions = decision_repo.list(filter_fn=lambda d: d.meeting_id == latest_m.id)
                actions = action_item_repo.list(filter_fn=lambda a: a.meeting_id == latest_m.id)
                transcripts = transcript_repo.list(filter_fn=lambda t: t.meeting_id == latest_m.id)
                content_text = (
                    f"PROJECT REQUIREMENTS SPECIFICATION: {clean_mt}\n\n"
                    f"Executive Summary:\n{summaries[0].content if summaries else ''}\n\n"
                    "Architectural Decisions:\n" + "\n".join(f"• {d.text}" for d in decisions) + "\n\n"
                    "Action Items & Deliverables:\n" + "\n".join(f"• {a.text}" for a in actions) + "\n\n"
                    "Transcript Extract:\n" + " ".join(t.text for t in transcripts[:30])
                )
                if doc_name in ("Uploaded Specification", "Document", "Enterprise SDLC Specification"):
                    doc_name = f"{clean_mt} Specification" if "specification" not in clean_mt.lower() else clean_mt

    # Ensure doc_name is cleaned of any BRD reference
    doc_name = re.sub(r'\bBRD\b\s*[-—–:]*\s*', '', doc_name, flags=re.IGNORECASE).strip() or "Requirements Specification"

    dim_list: List[str] = []
    if dimensions:
        try:
            dim_list = json.loads(dimensions) if dimensions.startswith("[") else [d.strip() for d in dimensions.split(",")]
        except Exception:
            dim_list = [d.strip() for d in dimensions.split(",")]

    user_id = getattr(current_user, "id", "user-1")
    review = await scoring_controller.evaluate_document(
        document_text=content_text,
        document_name=doc_name,
        rubric=rubric or "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)",
        dimensions=dim_list if dim_list else None,
        user_id=user_id,
    )
    return {
        "id": review.id,
        "review_id": review.id,
        "documentName": review.document_name,
        "overallScore": review.overall_score,
        "grade": review.grade,
        "scoringProfile": review.scoring_profile,
        "criticalGapsCount": review.critical_gaps_count,
        "actionItemsCount": review.action_items_count,
    }


@router.get("/{review_id}")
async def get_review(review_id: str, current_user=Depends(get_current_user)):
    return await scoring_controller.get_review(review_id)


@router.get("/{review_id}/score")
async def get_score(review_id: str, current_user=Depends(get_current_user)):
    return await scoring_controller.get_review(review_id)


@router.get("/{review_id}/criteria")
async def get_criteria(review_id: str, current_user=Depends(get_current_user)):
    return await scoring_controller.get_criteria(review_id)


@router.get("/{review_id}/gaps")
async def get_gaps(review_id: str, current_user=Depends(get_current_user)):
    return await scoring_controller.get_gaps(review_id)


@router.get("/{review_id}/recommendations")
async def get_recommendations(review_id: str, current_user=Depends(get_current_user)):
    return await scoring_controller.get_recommendations(review_id)


@router.post("/gaps/{gap_id}/apply-suggestion")
def apply_suggestion(gap_id: str, payload: ApplyGapSuggestionRequest, current_user=Depends(get_current_user)):
    return scoring_controller.apply_suggestion(gap_id, payload)


@router.post("/gaps/{gap_id}/dismiss")
def dismiss(gap_id: str, current_user=Depends(get_current_user)):
    return scoring_controller.dismiss(gap_id)


@router.get("/{review_id}/export-pdf")
async def export_scoring_pdf(review_id: str, current_user=Depends(get_current_user)):
    from fastapi.responses import Response
    from app.services.pdf_export_service import generate_scorecard_pdf, clean_title
    review_data = await scoring_controller.get_review(review_id)
    review_data["criteria"] = await scoring_controller.get_criteria(review_id)
    review_data["gaps"] = await scoring_controller.get_gaps(review_id)
    review_data["recommendations"] = await scoring_controller.get_recommendations(review_id)
    pdf_bytes = generate_scorecard_pdf(review_data)
    safe_name = re.sub(r'[^\w\s-]', '', review_data.get("documentName", "Scorecard")).strip().replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_Scorecard.pdf"'},
    )

