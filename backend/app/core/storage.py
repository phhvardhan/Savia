import threading
from enum import Enum
from pathlib import Path
from typing import Generic, List, Optional, Type, TypeVar
from pydantic import BaseModel


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
T = TypeVar("T", bound=BaseModel)




class EntityName(str, Enum):

    USERS = "users"
    WORKSPACES = "workspaces"
    WORKSPACE_MEMBERS = "workspace_members"
    MEETINGS = "meetings"
    RUNS = "runs"
    RUN_STEPS = "run_steps"
    TRANSCRIPTS = "transcripts"
    SUMMARIES = "summaries"
    DECISIONS = "decisions"
    ACTION_ITEMS = "action_items"
    STORIES = "stories"
    DOCUMENTS = "documents"
    DOCUMENT_SECTIONS = "document_sections"
    DOCUMENT_SOURCES = "document_sources"
    DOCUMENT_VERSIONS = "document_versions"
    DOCUMENT_GAPS = "document_gaps"
    TEMPLATES = "templates"
    TEMPLATE_SECTIONS = "template_sections"
    NOTIFICATIONS = "notifications"
    QUESTIONS = "questions"
    REVIEWS = "reviews"



class FileRepository(Generic[T]):
    """
    Generic NDJSON repository. Usage:

        user_repo = FileRepository(LocalUserProfile, EntityName.USERS)
        user_repo.add(new_user)
        user_repo.get(user_id)
        user_repo.list(filter_fn=lambda u: u.workspace_id == ws_id)
        user_repo.update(user_id, full_name="New Name")
        user_repo.delete(user_id)
    """

    def __init__(self, model_cls: Type[T], entity_name: EntityName):
        if not isinstance(entity_name, EntityName):
            raise TypeError(
                f"entity_name must be an EntityName enum member, got "
                f"{entity_name!r}. Only the fixed set defined in "
                f"EntityName is allowed — add a new member there first "
                f"if you genuinely need a new entity type."
            )

        self.model_cls = model_cls
        self.file_path = (DATA_DIR / f"{entity_name.value}.data.txt").resolve()
        self.file_path.touch(exist_ok=True)
        self._lock = threading.Lock()   

    def _read_all(self) -> List[T]:
        with self.file_path.open("r", encoding="utf-8", errors="replace") as f:
            return [self.model_cls.model_validate_json(line) for line in f if line.strip()]

    def _write_all(self, records: List[T]) -> None:
        with self.file_path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(r.model_dump_json() + "\n")

    def add(self, record: T) -> T:
        with self._lock:
            with self.file_path.open("a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")
        return record

    def get(self, record_id: str) -> Optional[T]:
        for r in self._read_all():
            if r.id == record_id:
                return r
        return None

    def list(self, filter_fn=None) -> List[T]:
        records = self._read_all()
        return [r for r in records if filter_fn(r)] if filter_fn else records

    def update(self, record_id: str, *args, **fields) -> Optional[T]:
        update_dict = {}
        if args and isinstance(args[0], dict):
            update_dict.update(args[0])
        update_dict.update(fields)
        with self._lock:
            records = self._read_all()
            updated = None
            for i, r in enumerate(records):
                if r.id == record_id:
                    updated = r.model_copy(update=update_dict)
                    records[i] = updated
                    break
            if updated:
                self._write_all(records)
            return updated

    def delete(self, record_id: str) -> bool:
        with self._lock:
            records = self._read_all()
            new_records = [r for r in records if r.id != record_id]
            if len(new_records) == len(records):
                return False
            self._write_all(new_records)
            return True