
from enum import Enum
from typing import List, Optional

from ..common_entity import BaseEntity


class DocumentType(str, Enum):
    BUSINESS_REQUIREMENTS = "business_requirements"   # BRD
    BRD = "brd"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


class SectionStatus(str, Enum):
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"
    EMPTY = "empty"


class Document(BaseEntity):
    workspace_id: str
    title: str                            # "Payments BRD v3"
    doc_type: DocumentType
    template_id: str
    status: DocumentStatus = DocumentStatus.DRAFT
    version_number: int = 1
    quality_score: int = 88
    word_count: int = 1200
    sections_count: int = 6
    sources_count: int = 2
    suggestion: Optional[dict] = None
    supersedes_document_id: Optional[str] = None   # links v3 -> v2
    generated_by_run_id: Optional[str] = None
    created_by: str
    published_at: Optional[str] = None
    published_by: Optional[str] = None


class DocumentSection(BaseEntity):
    document_id: str
    order: int
    title: str                          
    content: str
    word_count: int = 0
    status: SectionStatus = SectionStatus.EMPTY


class DocumentSourceType(str, Enum):
    MEETING_MINUTES = "meeting_minutes"
    JIRA_STORIES = "jira_stories"
    TEMPLATE = "template"


class DocumentSource(BaseEntity):
    """Traceability: what this document/section was built from."""
    document_id: str
    source_type: DocumentSourceType
    source_id: str                        # meeting_id / story batch id / template_id
    used_in_section_ids: List[str] = []


class DocumentVersionSnapshot(BaseEntity):
    document_id: str
    version_number: int
    section_snapshot: List[dict]          # frozen copy of sections at publish time
    published_by: str


class GapStatus(str, Enum):
    OPEN = "open"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class DocumentGap(BaseEntity):
    document_id: str
    section_id: str
    description: str                      # "Section 4 has no measurable non-functional requirements"
    suggested_text: Optional[str] = None
    status: GapStatus = GapStatus.OPEN
    scored_by_run_id: str


class DocumentReview(BaseEntity):
    workspace_id: str = "ws-1"
    document_name: str
    scoring_profile: str
    overall_score: int
    grade: str
    critical_gaps_count: int = 0
    action_items_count: int = 0
    dimensions: List[dict] = []
    section_ratings: List[dict] = []
    criteria: List[dict] = []
    gaps: List[dict] = []
    recommendations: List[dict] = []
    raw_document_text: Optional[str] = None
    created_by: Optional[str] = None