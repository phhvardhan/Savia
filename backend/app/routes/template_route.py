from fastapi import APIRouter, status

from app.controllers.template_controller import TemplateController
from app.schemas.entities.template_entity import Template, TemplateSectionDef
from app.schemas.requests.template_request import (
    TemplateCreateRequest,
    UpdateTemplateRequest,
    AddTemplateSection,
    UpdateTemplateSectionRequest,
)

router = APIRouter()
template_controller = TemplateController()



@router.post("/seed", response_model=Template)
def seed_default_templates():
    return template_controller.seed_default_templates()


@router.post("", response_model=Template, status_code=status.HTTP_201_CREATED)
def create_template(dto: TemplateCreateRequest):
    return template_controller.create_template(dto)


@router.get("", response_model=list[Template])
def list_templates():
    return template_controller.list_templates()


@router.get("/{template_id}", response_model=Template)
def get_template(template_id: str):
    return template_controller.get_template(template_id)


@router.put("/{template_id}", response_model=Template)
def update_template(template_id: str, dto: UpdateTemplateRequest):
    return template_controller.update_template(template_id, dto)


@router.delete("/{template_id}")
def delete_template(template_id: str):
    return template_controller.delete_template(template_id)



@router.post(
    "/sections", response_model=TemplateSectionDef, status_code=status.HTTP_201_CREATED
)
def add_section(dto: AddTemplateSection):
    return template_controller.add_section(dto)


@router.get("/{template_id}/sections", response_model=list[TemplateSectionDef])
def get_sections(template_id: str):
    return template_controller.get_sections(template_id)


@router.get("/{template_id}/sections/{section_id}", response_model=TemplateSectionDef)
def get_section(template_id: str, section_id: str):
    return template_controller.get_section(template_id, section_id)


@router.put("/{template_id}/sections/{section_id}", response_model=TemplateSectionDef)
def update_section(template_id: str, section_id: str, dto: UpdateTemplateSectionRequest):
    return template_controller.update_section(template_id, section_id, dto)


@router.delete("/{template_id}/sections/{section_id}")
def delete_section(template_id: str, section_id: str):
    return template_controller.delete_section(template_id, section_id)