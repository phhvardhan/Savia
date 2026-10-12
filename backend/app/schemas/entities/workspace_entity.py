from enum import Enum
from typing import Optional

from ..common_entity import BaseEntity


class WorkspaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Workspace(BaseEntity):
    name: str                      # e.g. "Digital Payments (DPX)"
    short_code: Optional[str] = None   # e.g. "DPX"
    description: Optional[str] = None


class WorkspaceMember(BaseEntity):
    workspace_id: str
    user_id: str
    role: WorkspaceRole = WorkspaceRole.MEMBER