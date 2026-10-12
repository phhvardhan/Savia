

from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.entities.workspace_entity import WorkspaceRole





class TemplateCreateRequest(BaseModel):

    name :str
    doc_type :str 
    version:Optional[str] ="v1"


class UpdateTemplateRequest(BaseModel):
    name :Optional[str]= None
    doc_type :Optional[str]= None
    version :Optional[str]= None


class UpdateTemplateSectionRequest(BaseModel):
    order :Optional[str]= None
    title :Optional[str]= None
    is_required :Optional[bool]= True
    guidance :Optional[str]= None



class AddTemplateSection(BaseModel):
    template_id: str
    order: int
    title: str
    is_required: bool = True
    guidance: str = ""       

    