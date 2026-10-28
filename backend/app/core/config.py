import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None, override=False)


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    value = _str(name)
    return int(value) if value else default


def _float(name: str, default: float) -> float:
    value = _str(name)
    return float(value) if value else default


def _bool(name: str, default: bool = False) -> bool:
    value = _str(name).lower()
    return value in ("1", "true", "yes", "on") if value else default


def _list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in _str(name, default).split(",") if item.strip()]


class Settings:
    PROJECT_NAME = "SAVIA"

    @property
    def LLM_PROVIDER(self) -> str:
        return _str("LLM_PROVIDER", "auto").lower() or "auto"

    @property
    def LLM_TIMEOUT_SECONDS(self) -> float:
        return _float("LLM_TIMEOUT_SECONDS", 120.0)

    @property
    def LLM_MAX_OUTPUT_TOKENS(self) -> int:
        return _int("LLM_MAX_OUTPUT_TOKENS", 8000)

    @property
    def LLM_TEMPERATURE(self) -> float:
        return _float("LLM_TEMPERATURE", 0.1)

    @property
    def LLM_RETRIES(self) -> int:
        return _int("LLM_RETRIES", 2)

    @property
    def LLM_INPUT_CHARS(self) -> int:
        return _int("LLM_INPUT_CHARS", 40000)

    @property
    def LLM_CHUNK_CHARS(self) -> int:
        return _int("LLM_CHUNK_CHARS", 16000)

    @property
    def LLM_CA_BUNDLE(self) -> str:
        return _str("LLM_CA_BUNDLE")

    @property
    def LLM_VERIFY_TLS(self) -> bool:
        return _bool("LLM_VERIFY_TLS", True)

    @property
    def GROQ_API_KEY(self) -> str:
        if self.LLM_PROVIDER == "azure_openai":
            return ""
        return _str("GROQ_API_KEY")

    @property
    def GROQ_MODELS(self) -> list[str]:
        return _list("GROQ_MODELS", "llama-3.3-70b-versatile,openai/gpt-oss-20b,llama-3.1-8b-instant")

    @property
    def AZURE_OPENAI_API_KEY(self) -> str:
        return _str("AZURE_OPENAI_API_KEY")

    @property
    def AZURE_OPENAI_ENDPOINT(self) -> str:
        return _str("AZURE_OPENAI_ENDPOINT").rstrip("/")

    @property
    def AZURE_OPENAI_DEPLOYMENT_NAME(self) -> str:
        return _str("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o") or "gpt-4o"

    @property
    def AZURE_OPENAI_API_VERSION(self) -> str:
        return _str("AZURE_OPENAI_API_VERSION", "2024-06-01") or "2024-06-01"

    @property
    def AZURE_OPENAI_URL(self) -> str:
        explicit = _str("AZURE_OPENAI_URL")
        if explicit:
            return explicit
        return (
            f"{self.AZURE_OPENAI_ENDPOINT}/openai/deployments/{self.AZURE_OPENAI_DEPLOYMENT_NAME}"
            f"/chat/completions?api-version={self.AZURE_OPENAI_API_VERSION}"
        )

    @property
    def OPENAI_API_KEY(self) -> str:
        if self.LLM_PROVIDER == "azure_openai":
            return ""
        return _str("OPENAI_API_KEY")

    @property
    def OPENAI_MODEL(self) -> str:
        return _str("OPENAI_MODEL", "gpt-4o") or "gpt-4o"

    @property
    def WHISPER_MODEL(self) -> str:
        return _str("WHISPER_MODEL", "tiny") or "tiny"

    @property
    def WHISPER_MODEL_PATH(self) -> Path:
        custom_path = _str("WHISPER_MODEL_PATH")
        if custom_path:
            return Path(custom_path)
        for name in ("faster-whisper-small.en", "faster-whisper-tiny"):
            local_repo_path = BASE_DIR / "models" / name
            if local_repo_path.exists():
                return local_repo_path
        return Path(self.WHISPER_MODEL)

    @property
    def UPLOAD_DIR(self) -> str:
        return _str("UPLOAD_DIR", "uploads") or "uploads"

    @property
    def DB_PATH(self) -> str:
        return _str("DB_PATH") or os.path.join(self.UPLOAD_DIR, "savia.db")

    @property
    def MAX_UPLOAD_MB(self) -> int:
        return _int("MAX_UPLOAD_MB", 300)

    @property
    def MAX_CONCURRENT_RUNS(self) -> int:
        return _int("MAX_CONCURRENT_RUNS", 4)

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return _list("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    @property
    def AUTH_REQUIRED(self) -> bool:
        return _bool("AUTH_REQUIRED", False)

    @property
    def ALLOW_OFFLINE_LOGIN(self) -> bool:
        return _bool("ALLOW_OFFLINE_LOGIN", False)

    @property
    def LDAP_SERVER(self) -> str:
        return _str("LDAP_SERVER")

    @property
    def LDAP_PORT(self) -> int:
        return _int("LDAP_PORT", 3269)

    @property
    def LDAP_BASE_DN(self) -> str:
        return _str("LDAP_BASE_DN")

    @property
    def LDAP_SERVICE_USER(self) -> str:
        return _str("LDAP_SERVICE_USER")

    @property
    def LDAP_SERVICE_PASSWORD(self) -> str:
        return _str("LDAP_SERVICE_PASSWORD")

    @property
    def ALLOWED_USERS(self) -> list[str]:
        return [u.lower() for u in _list("ALLOWED_USERS")]

    @property
    def LDAP_CA_CERT_FILE(self) -> str:
        custom_path = _str("LDAP_CA_CERT_FILE")
        if custom_path:
            if os.path.dirname(custom_path) == "":
                return str(BASE_DIR / "certs" / custom_path)
            return custom_path
        return str(BASE_DIR / "certs" / "JNJ_Private_2048bit_Root_CA_certificate.cer")

    @property
    def LDAP_TLS_VERSION(self) -> str:
        return _str("LDAP_TLS_VERSION", "TLSv1_2") or "TLSv1_2"

    @property
    def SECRET_KEY(self) -> str:
        return _str("SECRET_KEY")

    @property
    def ALGORITHM(self) -> str:
        return _str("ALGORITHM", "HS256") or "HS256"

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return _int("ACCESS_TOKEN_EXPIRE_MINUTES", 480)


settings = Settings()
