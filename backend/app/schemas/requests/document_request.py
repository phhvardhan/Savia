

from typing import List

from pydantic import BaseModel, Field, model_validator


class DocumentCreateRequest(BaseModel):
    workspace_id: str
    title: str = Field(..., min_length=3, max_length=200)
    template_id: str
    meeting_ids: List[str] = Field(..., min_length=1)
    story_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def at_least_one_source(self):
        if not self.meeting_ids and not self.story_ids:
            raise ValueError("A document needs at least one meeting or story source")
        return self


class DocumentGenerateRequest(BaseModel):
    workspace_id: str = "ws-1"
    title: str = "Enterprise Requirements Specification"
    doc_type: str = "BRD"
    standard: str = "Enterprise SDLC Standard v2.4"
    meeting_ids: List[str] = Field(default_factory=list)
    story_ids: List[str] = Field(default_factory=list)
    notes: str | None = None
    included_sections: List[str] = Field(default_factory=list)


class SectionRewriteRequest(BaseModel):
    instruction: str = Field(
        default="", max_length=1000,
        description="Optional extra guidance for the AI rewrite, e.g. 'make it shorter'"
    )


class SectionManualEditRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20_000)


class PublishDocumentRequest(BaseModel):
    confirm: bool = Field(..., description="Client must explicitly confirm — publishing cannot be undone")


class ApplyGapSuggestionRequest(BaseModel):
    accept_suggested_text: bool = True
    custom_text: str | None = Field(default=None, max_length=5_000)