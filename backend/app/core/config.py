import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


def _reload_env():
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    else:
        load_dotenv(override=True)


class Settings:
    PROJECT_NAME: str = "J&J Savia - Requirements to User Stories"

    @property
    def LLM_PROVIDER(self) -> str:
        _reload_env()
        return os.getenv("LLM_PROVIDER", "auto").lower()

    @property
    def HF_TOKEN(self) -> str:
        return os.getenv("HF_TOKEN", "")

    @property
    def GROQ_API_KEY(self) -> str:
        _reload_env()
        # LLM_PROVIDER=azure_openai means the J&J GenAI endpoint only: no Groq for chat or speech-to-text
        if self.LLM_PROVIDER == "azure_openai":
            return ""
        return os.getenv("GROQ_API_KEY", "").strip()

    @property
    def AZURE_OPENAI_API_KEY(self) -> str:
        _reload_env()
        return os.getenv("AZURE_OPENAI_API_KEY", "").strip()

    @property
    def AZURE_OPENAI_ENDPOINT(self) -> str:
        _reload_env()
        return os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()

    @property
    def AZURE_OPENAI_DEPLOYMENT_NAME(self) -> str:
        _reload_env()
        return os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o").strip()

    @property
    def AZURE_OPENAI_API_VERSION(self) -> str:
        _reload_env()
        return os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01").strip()

    @property
    def OPENAI_API_KEY(self) -> str:
        _reload_env()
        return os.getenv("OPENAI_API_KEY", "").strip()

    @property
    def OPENAI_MODEL(self) -> str:
        _reload_env()
        return os.getenv("OPENAI_MODEL", "gpt-4o").strip()

    @property
    def WHISPER_MODEL(self) -> str:
        _reload_env()
        return os.getenv("WHISPER_MODEL", "tiny").strip()

    @property
    def WHISPER_MODEL_PATH(self) -> Path:
        _reload_env()
        custom_path = os.getenv("WHISPER_MODEL_PATH", "").strip()
        if custom_path:
            return Path(custom_path)
        # Most accurate local model first; tiny is the small fallback
        for name in ("faster-whisper-small.en", "faster-whisper-tiny"):
            local_repo_path = BASE_DIR / "models" / name
            if local_repo_path.exists():
                return local_repo_path
        return Path(self.WHISPER_MODEL)

    @property
    def UPLOAD_DIR(self) -> str:
        return os.getenv("UPLOAD_DIR", "uploads")

    @property
    def TEMPORAL_ADDRESS(self) -> str:
        return os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

    @property
    def TEMPORAL_NAMESPACE(self) -> str:
        return os.getenv("TEMPORAL_NAMESPACE", "default")

    @property
    def TEMPORAL_TASK_QUEUE(self) -> str:
        return os.getenv("TEMPORAL_TASK_QUEUE", "savia")

    @property
    def STORAGE_BACKEND(self) -> str:
        return os.getenv("STORAGE_BACKEND", "local")

    @property
    def EXPORT_DIR(self) -> str:
        return os.getenv("EXPORT_DIR", "exports")

    @property
    def SESSION_FILE(self) -> str:
        return os.path.join(self.UPLOAD_DIR, "sessions.json")

    @property
    def JIRA_STORE_FILE(self) -> str:
        # Same folder, own JSON file — one row per user_id who has connected Jira
        return os.path.join(self.UPLOAD_DIR, "jira_connections.json")

    # ---- Old per-user LDAP "connect" flow (app/api/ldap.py, ldap_store.py) ----

    @property
    def LDAP_STORE_FILE(self) -> str:
        # Same pattern as JIRA_STORE_FILE — one row per user_id who has connected LDAP
        return os.path.join(self.UPLOAD_DIR, "ldap_connections.json")

    @property
    def LDAP_DEFAULT_PORT(self) -> int:
        _reload_env()
        return int(os.getenv("LDAP_DEFAULT_PORT", "389"))

    # ---- JNJ service-account LDAP login flow (app/api/auth_routes.py) ----

    @property
    def LDAP_SERVER(self) -> str:
        _reload_env()
        return os.getenv("LDAP_SERVER", "").strip()

    @property
    def LDAP_PORT(self) -> int:
        _reload_env()
        return int(os.getenv("LDAP_PORT", "3269"))

    @property
    def LDAP_BASE_DN(self) -> str:
        _reload_env()
        return os.getenv("LDAP_BASE_DN", "").strip()

    @property
    def LDAP_SERVICE_USER(self) -> str:
        _reload_env()
        return os.getenv("LDAP_SERVICE_USER", "").strip()

    @property
    def LDAP_SERVICE_PASSWORD(self) -> str:
        _reload_env()
        return os.getenv("LDAP_SERVICE_PASSWORD", "").strip()


    @property
    def ALLOWED_USERS(self) -> list[str]:
        """Comma-separated allowlist of usernames/emails permitted to log in,
        checked AFTER a successful AD bind. Empty list = no restriction."""
        _reload_env()
        raw = os.getenv("ALLOWED_USERS", "").strip()
        if not raw:
            return []
        return [u.strip().lower() for u in raw.split(",") if u.strip()]


    @property
    def LDAP_CA_CERT_FILE(self) -> str:
        """Absolute path to the JNJ root CA cert used to validate the LDAPS connection."""
        _reload_env()
        custom_path = os.getenv("LDAP_CA_CERT_FILE", "").strip()
        if custom_path:
            # If it's just a filename (no folder in it), assume it lives in certs/
            if os.path.dirname(custom_path) == "":
                return str(BASE_DIR / "certs" / custom_path)
            return custom_path
        return str(BASE_DIR / "certs" / "JNJ_Private_2048bit_Root_CA_certificate.cer")

    
    @property
    def LDAP_TLS_VERSION(self) -> str:
        _reload_env()
        return os.getenv("LDAP_TLS_VERSION", "TLSv1_2").strip()


    @property
    def SECRET_KEY(self) -> str:
        _reload_env()
        return os.getenv("SECRET_KEY", "").strip()

    @property
    def ALGORITHM(self) -> str:
        _reload_env()
        return os.getenv("ALGORITHM", "HS256").strip()

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        _reload_env()
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "90000"))


settings = Settings()