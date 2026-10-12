import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


def new_id() -> str:
    """UUID4 string — works as a flat-file primary key today and a
    Postgres UUID primary key tomorrow, unchanged."""
    return str(uuid.uuid4())


class BaseEntity(BaseModel):
    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  

    def to_json_line(self) -> str:
        """One line in data.txt = one record. Newline-delimited JSON (NDJSON)
        so appends are O(1) and the file stays streamable/greppable."""
        return self.model_dump_json()

    @classmethod
    def from_json_line(cls, line: str):
        return cls.model_validate_json(line)