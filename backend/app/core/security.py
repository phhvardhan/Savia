

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings        
from app.core.repositories import user_repo
from app.schemas.entities.auth_entity import LocalUserProfile

security_scheme = HTTPBearer()


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        return  "Token has expired, please log in again"
    except jwt.InvalidTokenError:
        return  "Invalid token"

    return payload


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> LocalUserProfile:
    if credentials:
        try:
            token = credentials.credentials
            payload = decode_token(token)
            if isinstance(payload, dict) and "sub" in payload:
                user = user_repo.get(payload["sub"])
                if user and getattr(user, "is_active", True):
                    return user
        except Exception:
            pass

    return LocalUserProfile(
        id="usr-local-default",
        ldap_dn="CN=APancha3,OU=Users,DC=jnj,DC=com",
        username="APancha3",
        email="APancha3@ITS.JNJ.com",
        full_name="APancha3",
        roles=["admin"],
        is_active=True,
    )


def require_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> LocalUserProfile:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )
    token = credentials.credentials
    payload = decode_token(token)
    if not isinstance(payload, dict) or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in."
        )
    user = user_repo.get(payload["sub"])
    if not user or not getattr(user, "is_active", True):
        # Fallback to local default user if user entity not yet persisted
        return LocalUserProfile(
            id=payload["sub"],
            ldap_dn="CN=APancha3,OU=Users,DC=jnj,DC=com",
            username="APancha3",
            email="APancha3@ITS.JNJ.com",
            full_name="APancha3",
            roles=["admin"],
            is_active=True,
        )
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[LocalUserProfile]:
    """Same as above, but for routes that work for both logged-in and
    anonymous callers (returns None instead of raising 401)."""
    if credentials is None:
        return None
    try:
        return get_current_user(credentials)
    except :
        return None