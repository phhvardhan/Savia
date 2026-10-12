from fastapi import HTTPException, status

from app.core.repositories import template_repo, template_section_repo
from app.schemas.entities.template_entity import Template, TemplateSectionDef
from app.schemas.requests.template_request import (
    TemplateCreateRequest,
    UpdateTemplateRequest,
    AddTemplateSection,
    UpdateTemplateSectionRequest,
)

DEFAULT_BRD_SECTIONS = [
    "Purpose and scope",
    "Business requirements",
    "Process flows",
    "Non-functional requirements",
    "Risks and assumptions",
    "Traceability to stories",
]


class TemplateService:

    def seed_default_templates(self) -> Template:
        existing = template_repo.list(filter_fn=lambda t: t.name == "J&J SDLC BRD v2")
        if existing:
            return existing[0]

        template = template_repo.add(Template(name="J&J SDLC BRD v2", doc_type="brd", version="v1"))

        section_ids = []
        for i, title in enumerate(DEFAULT_BRD_SECTIONS):
            section = template_section_repo.add(
                TemplateSectionDef(
                    template_id=template.id,
                    order=i,
                    title=title,
                    is_required=True,
                    guidance="",
                )
            )
            section_ids.append(section.id)

        return template_repo.update(template.id, section_ids=section_ids)

    def create_template(self, dto: TemplateCreateRequest) -> Template:
        template = Template(
            name=dto.name,
            doc_type=dto.doc_type,
            version=dto.version or "v1",
            section_ids=[],
        )
        return template_repo.add(template)

    def list_templates(self) -> list[Template]:
        return template_repo.list()

    def get_template(self, template_id: str) -> Template:
        template = template_repo.get(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )
        return template

    def update_template(self, template_id: str, dto: UpdateTemplateRequest) -> Template:
        self.get_template(template_id)
        update_fields = dto.model_dump(exclude_unset=True)
        return template_repo.update(template_id, **update_fields)

    def delete_template(self, template_id: str) -> None:
        self.get_template(template_id)
        # cascade delete all sections belonging to this template
        sections = template_section_repo.list(
            filter_fn=lambda s: s.template_id == template_id
        )
        for section in sections:
            template_section_repo.delete(section.id)
        template_repo.delete(template_id)


    def add_section(self, dto: AddTemplateSection) -> TemplateSectionDef:
        template = self.get_template(dto.template_id)

        section = template_section_repo.add(
            TemplateSectionDef(
                template_id=dto.template_id,
                order=dto.order,
                title=dto.title,
                is_required=dto.is_required,
                guidance=dto.guidance,
            )
        )

        section_ids = list(template.section_ids) + [section.id]
        template_repo.update(template.id, section_ids=section_ids)
        return section

    def get_sections(self, template_id: str) -> list[TemplateSectionDef]:

        self.get_template(template_id)
        sections = template_section_repo.list(
            filter_fn=lambda s: s.template_id == template_id
        )
        return sorted(sections, key=lambda s: s.order)

    def get_section(self, template_id: str, section_id: str) -> TemplateSectionDef:
        section = template_section_repo.get(section_id)
        if not section or section.template_id != template_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template section not found",
            )
        return section

    def update_section(
        self, template_id: str, section_id: str, dto: UpdateTemplateSectionRequest
    ) -> TemplateSectionDef:
        self.get_section(template_id, section_id)
        update_fields = dto.model_dump(exclude_unset=True)
        return template_section_repo.update(section_id, **update_fields)

    def delete_section(self, template_id: str, section_id: str) -> None:
        self.get_section(template_id, section_id)
        template_section_repo.delete(section_id)

        template = template_repo.get(template_id)
        if template:
            section_ids = [sid for sid in template.section_ids if sid != section_id]
            template_repo.update(template_id, section_ids=section_ids)


