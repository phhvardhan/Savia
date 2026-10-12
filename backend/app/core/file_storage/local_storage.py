import os
from pathlib import Path
from .base import StorageService
from app.core.config import settings

class LocalStorageService(StorageService):
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_bytes: bytes, filename: str) -> str:
        file_path = self.upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return str(file_path)

    def delete(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)

    def get_path(self, path: str) -> str:
        return path 