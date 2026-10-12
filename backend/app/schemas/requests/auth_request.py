from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):

    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)

    @field_validator("username")
    @classmethod
    def username_no_whitespace(cls, v: str) -> str:
        if v != v.strip():
            raise ValueError("username must not have leading/trailing whitespace")
        return v


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    department: Optional[str]
    roles: List[str]
    workspace_id: Optional[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"