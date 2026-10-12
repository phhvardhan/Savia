from abc import ABC, abstractmethod

class StorageService(ABC):
  

    @abstractmethod
    def save(self, file_bytes: bytes, filename: str) -> str:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass

    @abstractmethod
    def get_path(self, path: str) -> str:
        pass