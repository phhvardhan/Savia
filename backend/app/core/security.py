from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.repositories import user_repo
from app.schemas.entities.auth_entity import LocalUserProfile

bearer = HTTPBearer(auto_error=False)

LOCAL_USER = LocalUserProfile.model_construct(
    id="usr-local",
    ldap_dn="",
    username="local-user",
    email="local-user@localhost",
    department=None,
    workspace_id=None,
    full_name="Local user",
    roles=["member"],
    is_active=True,
)


def create_access_token(user_id: str) -> str:
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set in backend/.env.")
    now = datetime.utcnow()
    payload = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _user_from_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[LocalUserProfile]:
    if not credentials or not settings.SECRET_KEY:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    user = user_repo.get(payload.get("sub", ""))
    return user if user and getattr(user, "is_active", True) else None


def require_authenticated_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> LocalUserProfile:
    user = _user_from_token(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> LocalUserProfile:
    if settings.AUTH_REQUIRED:
        return require_authenticated_user(credentials)
    return _user_from_token(credentials) or LOCAL_USER
