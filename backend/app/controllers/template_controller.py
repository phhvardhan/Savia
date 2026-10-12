from app.services.template_service import TemplateService
from app.schemas.entities.template_entity import Template, TemplateSectionDef
from app.schemas.requests.template_request import (
    TemplateCreateRequest,
    UpdateTemplateRequest,
    AddTemplateSection,
    UpdateTemplateSectionRequest,
)

service =TemplateService()

class TemplateController:

    def create_template(self, dto: TemplateCreateRequest) -> Template:
        return service.create_template(dto)

    def list_templates(self) -> list[Template]:
        return service.list_templates()

    def get_template(self, template_id: str) -> Template:
        return service.get_template(template_id)

    def update_template(self, template_id: str, dto: UpdateTemplateRequest) -> Template:
        return service.update_template(template_id, dto)

    def delete_template(self, template_id: str) -> dict:
        service.delete_template(template_id)
        return {"message": "Template deleted successfully"}

    def seed_default_templates(self) -> Template:
        return service.seed_default_templates()

    def add_section(self, dto: AddTemplateSection) -> TemplateSectionDef:
        return service.add_section(dto)

    def get_sections(self, template_id: str) -> list[TemplateSectionDef]:
        return service.get_sections(template_id)

    def get_section(self, template_id: str, section_id: str) -> TemplateSectionDef:
        return service.get_section(template_id, section_id)

    def update_section(
        self, template_id: str, section_id: str, dto: UpdateTemplateSectionRequest
    ) -> TemplateSectionDef:
        return service.update_section(template_id, section_id, dto)

    def delete_section(self, template_id: str, section_id: str) -> dict:
        service.delete_section(template_id, section_id)
        return {"message": "Template section deleted successfully"}


