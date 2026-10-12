from app.services.workspace_service import WorkspaceService
from app.schemas.entities.workspace_entity import Workspace, WorkspaceMember
from app.schemas.requests.workspace_request import (
    WorkspaceCreateRequest,
    UpdateWorkspaceRequest,
    AddMemberToWorkspace,
)
from app.utils.response import success_response, error_response


service = WorkspaceService()


class WorkspaceController:



    async def create_workspace(self, dto: WorkspaceCreateRequest, owner_id: str) -> Workspace:
        try:
            data= await service.create(dto, owner_id)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)

  
    async def get_all(self) -> list[Workspace]:
        try:
            data= await service.get_all()
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)

        

    async def get_workspace(self, workspace_id: str) -> Workspace:

        try:
            data= await service.get_by_id(workspace_id)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)
        
        

    async def get_workspace_members(self, workspace_id: str) -> list[WorkspaceMember]:
        try:
            data= await service.get_members(workspace_id)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)


         

    async def update_workspace(self, workspace_id: str, dto: UpdateWorkspaceRequest) -> Workspace:
        try:
            data= await service.update(workspace_id, dto)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)

          

    async def add_member(self, workspace_id: str, dto: AddMemberToWorkspace) -> WorkspaceMember:
        try:
            data= await service.add_member(workspace_id, dto)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)        
        

    async def delete_member(self, workspace_id: str, user_id: str) -> None:


        try:
            data= await service.delete_member(workspace_id, user_id)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)
        
        


