from app.core.config import settings
from .local_storage import LocalStorageService


def get_storage_service() -> LocalStorageService:
    if settings.STORAGE_BACKEND.strip() == "local":
        return LocalStorageService()
        
    raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")