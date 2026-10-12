
from typing import List

from ..common_entity import BaseEntity


class TemplateSectionDef(BaseEntity):
    template_id: str
    order: int
    title: str
    is_required: bool = True
    guidance: str = ""          # instructions the AI follows when drafting this section


class Template(BaseEntity):
    name: str                   # "J&J SDLC BRD v2"
    doc_type: str               # matches DocumentType
    version: str = "v1"
    section_ids: List[str] = []