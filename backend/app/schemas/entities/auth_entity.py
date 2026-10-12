
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from ..common_entity import BaseEntity


class LDAPProfile(BaseModel):
    """Not persisted — just the shape of what we read from LDAP right
    after a successful bind, before mapping it into LocalUserProfile."""
    dn: str
    uid: str
    email: EmailStr
    full_name: str
    department: Optional[str] = None
    groups: List[str] = Field(default_factory=list)


class LocalUserProfile(BaseEntity):
    """The persisted record — cached/synced copy of the LDAP identity.
    Every other entity's owner_id/created_by/uploaded_by points at this."""
    ldap_dn: str
    username: str
    email: EmailStr
    full_name: str
    department: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    workspace_id: Optional[str] = None
    avatar_initials: Optional[str] = None
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True