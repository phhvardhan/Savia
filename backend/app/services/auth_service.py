from datetime import datetime
from app.core.ldap import authenticate_user
from app.core.repositories import user_repo
from app.core.security import create_access_token
from app.schemas.entities.auth_entity import LocalUserProfile
from app.schemas.requests.auth_request import LoginRequest, TokenResponse


AD_GROUP_ROLE_MAP = {
    "ITS-APP-ODAllowProvisioning-AP": "admin",
    "CBT-PR-Automatius-JJLearn-APP-Employee": "member",
}
DEFAULT_ROLE = "member"


def _map_groups_to_roles(ad_groups: list[str]) -> list[str]:
    roles = {AD_GROUP_ROLE_MAP[g] for g in ad_groups if g in AD_GROUP_ROLE_MAP}
    return list(roles) or [DEFAULT_ROLE]


def _find_existing_user(identifier: str) -> LocalUserProfile | None:

    matches = user_repo.list(filter_fn=lambda u: u.username == identifier)
    return matches[0] if matches else None


def _create_or_sync_user(ldap_data: dict) -> LocalUserProfile:

    identifier = ldap_data["identifier"]

    roles = _map_groups_to_roles(ldap_data.get("ad_groups", []))

    existing = _find_existing_user(identifier)

    if existing is None:

        new_user = LocalUserProfile(
            ldap_dn=ldap_data["dn"],
            username=identifier,
            email=ldap_data.get("email") or f"{identifier}",
            full_name=ldap_data["display_name"],
            roles=roles,
            last_synced_at=datetime.utcnow(),
            is_active=True,
        )
        return user_repo.add(new_user)


    return user_repo.update(
        existing.id,
        full_name=ldap_data["display_name"],
        email=ldap_data.get("email") or existing.email,
        roles=roles,
        last_synced_at=datetime.utcnow(),
    )


class AuthService:

    async def login(self, body: LoginRequest) -> TokenResponse:

        ldap_data = await authenticate_user(body.username, body.password)
        user = _create_or_sync_user(ldap_data)
        return TokenResponse(access_token=create_access_token(user.id))