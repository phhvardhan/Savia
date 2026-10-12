from fastapi import HTTPException, status

from app.services.document_service import DocumentService
from app.schemas.requests.document_request import (
    DocumentCreateRequest, DocumentGenerateRequest, SectionManualEditRequest, SectionRewriteRequest, PublishDocumentRequest,
)
from app.utils.response import success_response, error_response

document_service = DocumentService()


class DocumentController:
    async def generate_document(self, payload: DocumentGenerateRequest, user):
        return await document_service.generate_document(payload, user)

    def create_document(self, payload: DocumentCreateRequest, user):
        return document_service.create_document(payload, user)

    def list_documents(self, workspace_id: str):
        return document_service.list_documents(workspace_id)

    def get_document(self, document_id: str):
        return document_service.get_document(document_id)

    def get_sections(self, document_id: str):
        return document_service.get_sections(document_id)

    def get_sources(self, document_id: str):
        return document_service.get_sources(document_id)

    def get_history(self, document_id: str):
        return document_service.get_history(document_id)

    def edit_section_manual(self, section_id: str, payload: SectionManualEditRequest):
        return document_service.edit_section_manual(section_id, payload)

    async def rewrite_section(self, section_id: str, payload: SectionRewriteRequest):
        return await document_service.rewrite_section(section_id, payload)

    def regenerate(self, document_id: str, user):
        return document_service.regenerate(document_id, user)

    def publish(self, document_id: str, payload: PublishDocumentRequest, user):
        return document_service.publish(document_id, payload, user)

    def export(self, document_id: str):
        return document_service.export(document_id)
