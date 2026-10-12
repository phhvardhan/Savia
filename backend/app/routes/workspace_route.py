from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.controllers.workspace_controller import WorkspaceController
from app.schemas.entities.workspace_entity import Workspace, WorkspaceMember
from app.schemas.requests.workspace_request import WorkspaceCreateRequest,UpdateWorkspaceRequest,AddMemberToWorkspace

router = APIRouter()
workspace_controller = WorkspaceController()

 


@router.post("", response_model=Workspace)
def create_workspace(dto: WorkspaceCreateRequest, owner_id: str):
    return workspace_controller.create_workspace(dto, owner_id)
 
 

@router.get("/{workspace_id}", response_model=Workspace)
def get_workspace(workspace_id: str):
    return workspace_controller.get_workspace(workspace_id)

@router.get("/", response_model=list[Workspace])
def get_all():
    return workspace_controller.get_all()


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMember])
def get_workspace_members(workspace_id: str):
    return workspace_controller.get_workspace_members(workspace_id)
 
 
@router.patch("/{workspace_id}", response_model=Workspace)
def update_workspace(workspace_id: str, dto: UpdateWorkspaceRequest):
    return workspace_controller.update_workspace(workspace_id, dto)
 
 

@router.post("/{workspace_id}/members", response_model=WorkspaceMember)
def add_member(workspace_id: str, dto: AddMemberToWorkspace):
    return workspace_controller.add_member(workspace_id, dto)
 
 
@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
def delete_member(workspace_id: str, user_id: str):
    return workspace_controller.delete_member(workspace_id, user_id)
 