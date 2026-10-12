

from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.entities.workspace_entity import WorkspaceRole



class WorkspaceCreateRequest(BaseModel):

    name :str
    short_code :Optional[str] =None 
    description:Optional[str] =None


class UpdateWorkspaceRequest(BaseModel):
    name :Optional[str]= None
    short_code :Optional[str]= None
    description :Optional[str]= None


class AddMemberToWorkspace(BaseModel):
    user_id :str
    role :Optional[WorkspaceRole]= WorkspaceRole.MEMBER
    
    
    


