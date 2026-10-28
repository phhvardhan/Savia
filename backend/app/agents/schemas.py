from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

FIBONACCI = {1, 2, 3, 5, 8, 13, 21}


class Loose(BaseModel):
    model_config = ConfigDict(extra="allow")


def _text_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text.lower() in ("null", "none", "n/a", "tbd") else text


class MomRaw(Loose):
    discussion_summary: Optional[str] = None
    attendees: List[Any]
    key_points: List[Any]
    requirements_identified: List[Any]
    decisions_finalized: List[Any]
    action_items: List[Any]
    open_questions: List[Any]


class AcceptanceCriterion(Loose):
    given: Optional[str] = None
    when: Optional[str] = None
    then: Optional[str] = None


class UserStory(Loose):
    user_story_id: Optional[str] = None
    epic: Optional[str] = None
    title: str
    description: Optional[str] = None
    as_a: Optional[str] = None
    i_want: Optional[str] = None
    so_that: Optional[str] = None
    acceptance_criteria: List[Union[AcceptanceCriterion, str]] = Field(default_factory=list)
    story_points: Optional[int] = None
    priority: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    requirement_ids: List[str] = Field(default_factory=list)

    @field_validator("story_points", mode="before")
    @classmethod
    def _points(cls, value: Any) -> Optional[int]:
        try:
            points = int(float(value))
        except (TypeError, ValueError):
            return None
        return points if points in FIBONACCI else None


class AgileStoriesOutput(Loose):
    epics: List[str]
    user_stories: List[UserStory]
    open_questions: List[Any] = Field(default_factory=list)


class SolutionOutput(Loose):
    title: Optional[str] = None
    executive_summary: Optional[str] = None
    problem: Any = None
    constraints: List[Any] = Field(default_factory=list)
    proposed_solution: Any = None
    components: List[Any]
    integrations: List[Any] = Field(default_factory=list)
    alternatives: List[Any] = Field(default_factory=list)
    risks: List[Any] = Field(default_factory=list)
    roadmap: List[Any] = Field(default_factory=list)
    needs_info: List[Any] = Field(default_factory=list)


class GapOutput(Loose):
    title: Optional[str] = None
    summary: Optional[str] = None
    traceability_matrix: List[Any]
    gap_classification: List[Any]
    unmet_requirements_and_impact: List[Any] = Field(default_factory=list)


class Ddl3Output(Loose):
    design_id: Optional[str] = None
    title: Optional[str] = None
    purpose: Optional[str] = None
    scope: Any = None
    functional_flow: List[Any]
    business_rules: List[Any] = Field(default_factory=list)
    validation_rules: List[Any] = Field(default_factory=list)
    api_requirements: List[Any] = Field(default_factory=list)
    error_handling: List[Any] = Field(default_factory=list)
    open_questions: List[Any] = Field(default_factory=list)


class KddOutput(Loose):
    title: Optional[str] = None
    executive_dossier: Optional[str] = None
    architectural_governance: Any = None
    decision_making_framework: List[Any]
    enterprise_compliance_and_audit: Any = None


class ChangeImpactOutput(Loose):
    title: Optional[str] = None
    executive_summary: Optional[str] = None
    cross_platform_impact_analysis: Any = None
    cross_workstream_dependencies: List[Any]
    operational_readiness_evaluation: Any = None
    interdependency_matrix: List[Any]


class TestCase(Loose):
    test_case_id: Optional[str] = None
    title: str
    type: Optional[str] = None
    category: Optional[str] = None
    requirement_id: Optional[str] = None
    user_story_id: Optional[str] = None
    design_id: Optional[str] = None
    preconditions: List[Any] = Field(default_factory=list)
    test_steps: List[Any]
    expected_result: Optional[str] = None
    priority: Optional[str] = None

    @field_validator("requirement_id", "user_story_id", "design_id", "priority", "expected_result", mode="before")
    @classmethod
    def _clean(cls, value: Any) -> Optional[str]:
        return _text_or_none(value)


class TestOutput(Loose):
    test_summary: Any = None
    test_inventory: List[Any] = Field(default_factory=list)
    test_cases: List[TestCase]
    test_plan: Any = None
    open_questions: List[Any] = Field(default_factory=list)


class Dimension(Loose):
    id: Optional[str] = None
    name: str
    score: int = Field(ge=0, le=100)
    weight: int = Field(default=20, ge=0, le=100)
    rating: Optional[str] = None
    summary: Optional[str] = None


class StageJudgement(Loose):
    sdlc_stage: str
    stage_score: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[str] = None
    justification: str
    key_deficits: List[str] = Field(default_factory=list)
    remediation_action: Optional[str] = None


class Justification(Loose):
    overall_summary: str
    sdlc_stage_breakdown: List[StageJudgement]


class AuditOutput(Loose):
    dimensions: List[Dimension] = Field(min_length=1)
    sdlc_score_justification: Justification
    sectionRatings: List[Any] = Field(default_factory=list)
    criteria: List[Any] = Field(default_factory=list)
    gaps: List[Any] = Field(default_factory=list)
    recommendations: List[Any] = Field(default_factory=list)
