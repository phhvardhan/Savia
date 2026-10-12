
# POST   /documents                       # create BRD: {meeting_ids[], story_ids[], template_id, doc_type}
# GET    /documents                       # list (workspace document library)
# GET    /documents/{id}
# GET    /documents/{id}/sections
# PATCH  /documents/{id}/sections/{section_id}    # manual edit / "Rewrite" AI action
# POST   /documents/{id}/sections/{section_id}/rewrite   # AI rewrite of one section
# GET    /documents/{id}/sources          # traceability: which meetings/stories/template built this
# GET    /documents/{id}/history          # version history (v1, v2, v3…)
# POST   /documents/{id}/regenerate       # full regen from sources
# POST   /documents/{id}/publish          # body confirms: adds to library, notifies reviewers, supersedes prior version
# GET    /documents/{id}/export           # PDF/DOCX export
# POST   /documents/{id}/share








# POST   /documents/{id}/score            # runs Document Scoring Agent
# GET    /documents/{id}/gaps             # list of flagged issues w/ suggested fix text
# POST   /documents/{id}/gaps/{gap_id}/apply-suggestion
# POST   /documents/{id}/gaps/{gap_id}/dismiss
















from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.core.security import get_current_user
from app.controllers.document_controller import DocumentController
from app.schemas.entities.document_entity import Document, DocumentSection, DocumentSource, DocumentVersionSnapshot
from app.schemas.requests.document_request import (
    DocumentCreateRequest, DocumentGenerateRequest, SectionManualEditRequest, SectionRewriteRequest, PublishDocumentRequest,
)

router = APIRouter()
document_controller = DocumentController()


@router.post("/generate", response_model=Document)
async def generate_document(payload: DocumentGenerateRequest, current_user=Depends(get_current_user)):
    return await document_controller.generate_document(payload, current_user)


@router.post("/", response_model=Document)
async def create_document(payload: DocumentCreateRequest, current_user=Depends(get_current_user)):
    return document_controller.create_document(payload, current_user)


@router.get("/", response_model=list[Document])
async def list_documents(workspace_id: str, current_user=Depends(get_current_user)):
    return document_controller.list_documents(workspace_id)


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str, current_user=Depends(get_current_user)):
    return document_controller.get_document(document_id)


@router.get("/{document_id}/sections", response_model=list[DocumentSection])
async def get_sections(document_id: str, current_user=Depends(get_current_user)):
    return document_controller.get_sections(document_id)


@router.patch("/sections/{section_id}", response_model=DocumentSection)
async def edit_section(section_id: str, payload: SectionManualEditRequest, current_user=Depends(get_current_user)):
    return document_controller.edit_section_manual(section_id, payload)


@router.post("/sections/{section_id}/rewrite", response_model=DocumentSection)
async def rewrite_section(section_id: str, payload: SectionRewriteRequest, current_user=Depends(get_current_user)):
    return document_controller.rewrite_section(section_id, payload)


@router.get("/{document_id}/sources", response_model=list[DocumentSource])
async def get_sources(document_id: str, current_user=Depends(get_current_user)):
    return document_controller.get_sources(document_id)


@router.get("/{document_id}/history", response_model=list[DocumentVersionSnapshot])
async def get_history(document_id: str, current_user=Depends(get_current_user)):
    return document_controller.get_history(document_id)


@router.post("/{document_id}/regenerate", response_model=Document)
async def regenerate(document_id: str, current_user=Depends(get_current_user)):
    return document_controller.regenerate(document_id, current_user)


@router.post("/{document_id}/publish", response_model=Document)
async def publish(document_id: str, payload: PublishDocumentRequest, current_user=Depends(get_current_user)):
    return document_controller.publish(document_id, payload, current_user)


@router.post("/{document_id}/approve", response_model=Document)
async def approve_document(document_id: str, current_user=Depends(get_current_user)):
    payload = PublishDocumentRequest(confirm=True)
    return document_controller.publish(document_id, payload, current_user)


@router.get("/{document_id}/export", response_class=PlainTextResponse)
async def export(document_id: str, current_user=Depends(get_current_user)):
    return document_controller.export(document_id)


@router.get("/{document_id}/export-pdf")
async def export_document_pdf(document_id: str, current_user=Depends(get_current_user)):
    import re
    from fastapi import HTTPException
    from fastapi.responses import Response
    from app.core.repositories import document_repo, document_section_repo
    from app.services.pdf_export_service import generate_document_pdf
    doc = document_repo.get(document_id)
    if not doc:
        docs = document_repo.list()
        doc = docs[-1] if docs else None
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = document_section_repo.list(filter_fn=lambda s: s.document_id == doc.id)
    pdf_bytes = generate_document_pdf(
        title=doc.title,
        version=str(doc.version_number),
        quality_score=doc.quality_score,
        sections=[s.__dict__ for s in sections]
    )
    safe_name = re.sub(r'[^\w\s-]', '', doc.title).strip().replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_Specification.pdf"'},
    )


@router.post("/{document_id}/share", status_code=204)
async def share(document_id: str, current_user=Depends(get_current_user)):
    # TODO: wire up real notification/email dispatch to reviewers
    return None
