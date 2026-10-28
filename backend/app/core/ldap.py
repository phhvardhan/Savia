import os
import ssl

from ldap3 import ALL, SUBTREE, Connection, Server, Tls
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError
from ldap3.utils.conv import escape_filter_chars
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.utils.logger import logger

AD_REASONS = {
    "data 52e": "Invalid credentials.",
    "data 532": "Password has expired.",
    "data 533": "Account is disabled.",
    "data 701": "Account has expired.",
    "data 773": "Password must be changed before first use.",
    "data 775": "Account is locked out.",
}


class DirectoryUnavailable(Exception):
    pass


def _server() -> Server:
    ca_file = settings.LDAP_CA_CERT_FILE
    if not os.path.exists(ca_file):
        raise DirectoryUnavailable(f"LDAP CA certificate not found at {ca_file}.")
    tls_version = getattr(ssl, f"PROTOCOL_{settings.LDAP_TLS_VERSION}", ssl.PROTOCOL_TLS_CLIENT)
    tls = Tls(ca_certs_file=ca_file, validate=ssl.CERT_REQUIRED, version=tls_version)
    return Server(settings.LDAP_SERVER, port=settings.LDAP_PORT, use_ssl=True, tls=tls, get_info=ALL, connect_timeout=5)


def _find_user_entry(identifier: str):
    server = _server()
    try:
        conn = Connection(server, user=settings.LDAP_SERVICE_USER, password=settings.LDAP_SERVICE_PASSWORD, auto_bind=True)
    except LDAPSocketOpenError as e:
        raise DirectoryUnavailable(f"Could not reach {settings.LDAP_SERVER}:{settings.LDAP_PORT}: {e}")
    except LDAPBindError as e:
        raise DirectoryUnavailable(f"Service account bind failed: {e}")
    try:
        safe = escape_filter_chars(identifier)
        conn.search(
            search_base=settings.LDAP_BASE_DN,
            search_filter=f"(&(objectClass=user)(|(sAMAccountName={safe})(mail={safe})))",
            search_scope=SUBTREE,
            attributes=["distinguishedName", "displayName", "mail", "memberOf"],
        )
        if not conn.entries:
            raise ValueError("Invalid credentials.")
        return conn.entries[0], server
    finally:
        conn.unbind()


def _groups(user_entry) -> list[str]:
    if not hasattr(user_entry, "memberOf"):
        return []
    return [dn.split(",")[0].replace("CN=", "") for dn in user_entry.memberOf]


def _allowed(identifier: str) -> bool:
    allowed = settings.ALLOWED_USERS
    return not allowed or identifier.lower() in allowed


def _bind(identifier: str, password: str) -> dict:
    user_entry, server = _find_user_entry(identifier)
    conn = Connection(server, user=user_entry.entry_dn, password=password, authentication="SIMPLE")
    if not conn.bind():
        message = conn.result.get("message", "")
        reason = next((r for code, r in AD_REASONS.items() if code in message), "Invalid credentials.")
        raise ValueError(reason)
    conn.unbind()
    return {
        "identifier": identifier,
        "dn": user_entry.entry_dn,
        "display_name": user_entry.displayName.value if hasattr(user_entry, "displayName") else identifier,
        "email": user_entry.mail.value if hasattr(user_entry, "mail") and user_entry.mail else None,
        "ad_groups": _groups(user_entry),
    }


async def authenticate_user(identifier: str, password: str) -> dict:
    identifier = (identifier or "").strip()
    if not identifier or not password:
        raise ValueError("Username and password are required.")
    if not _allowed(identifier):
        raise ValueError("This account is not allowed to use SAVIA.")
    try:
        return await run_in_threadpool(_bind, identifier, password)
    except DirectoryUnavailable as e:
        if settings.ALLOW_OFFLINE_LOGIN and settings.ALLOWED_USERS and _allowed(identifier):
            logger.warning(f"[LDAP] Directory unavailable ({e}); offline login for allowlisted '{identifier}'.")
            return {"identifier": identifier, "dn": "", "display_name": identifier, "email": None, "ad_groups": []}
        logger.warning(f"[LDAP] Directory unavailable: {e}")
        raise ValueError("Cannot reach the corporate directory from this network.")
