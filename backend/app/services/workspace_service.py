from datetime import datetime, timezone
from fastapi import HTTPException, status


from app.core.repositories import workspace_repo, workspace_member_repo
from app.schemas.entities.workspace_entity import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.requests.workspace_request import (
    WorkspaceCreateRequest,
    UpdateWorkspaceRequest,
    AddMemberToWorkspace,
)


class WorkspaceService:

    async def create(self, dto: WorkspaceCreateRequest, owner_id: str) -> Workspace:
      
        workspace = Workspace(
            name=dto.name,
            short_code=dto.short_code,
            description=dto.description,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
        )
        return workspace_repo.add(workspace)

    async def get_by_id(self, id: str) -> Workspace:
        ws = workspace_repo.get(id)
        if not ws:
            return "Workspace not found"
        return ws

    async def get_members(self, id: str) -> list[WorkspaceMember]:
        return workspace_member_repo.list(filter_fn=lambda m: m.workspace_id == id)

    async def update(self, id: str, dto: UpdateWorkspaceRequest) -> Workspace:
        ws = workspace_repo.get(id)
        if not ws:
            return "Workspace not found"

        update_fields = dto.model_dump(exclude_unset=True)
        updated = workspace_repo.update(id, **update_fields)
        return updated

    async def add_member(self, workspace_id: str, dto: AddMemberToWorkspace) -> WorkspaceMember:
        ws = workspace_repo.get(workspace_id)
        if not ws:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        already_member = workspace_member_repo.list( filter_fn=lambda m: m.workspace_id == workspace_id and m.user_id == dto.user_id )
        if already_member:
            raise "User is already a member"

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=dto.user_id,
            role=dto.role or WorkspaceRole.MEMBER,
        )
        return workspace_member_repo.add(member)

    async def delete_member(self, workspace_id: str, user_id: str) -> None:
    
        members = workspace_member_repo.list(
            filter_fn=lambda m: m.workspace_id == workspace_id and m.user_id == user_id
        )
        if not members:
            raise "Member not found"
        
        workspace_member_repo.remove(members[0].id)