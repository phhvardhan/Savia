from typing import Tuple
from app.models.workflow import WorkflowSession, StageEnum, ApprovalStatus


STAGE_ORDER = [
    StageEnum.INGESTION,
    StageEnum.REQUIREMENTS,
    StageEnum.MOM,
    StageEnum.USER_STORY,
    StageEnum.DDL3,
    StageEnum.TESTING,
    StageEnum.COMPLETED,
]

STAGE_PREREQUISITES = {
    StageEnum.MOM: [],
    StageEnum.USER_STORY: [StageEnum.REQUIREMENTS, StageEnum.MOM],
    StageEnum.DDL3: [StageEnum.REQUIREMENTS, StageEnum.USER_STORY],
    StageEnum.TESTING: [StageEnum.REQUIREMENTS, StageEnum.USER_STORY, StageEnum.DDL3],
}


def can_advance(session: WorkflowSession, target_stage: StageEnum, bypass_approval: bool = False) -> Tuple[bool, str]:
    """Pure gate check. SdlcWorkflow runs it inside its update validators, so it must stay deterministic."""
    if session.current_stage == target_stage:
        return True, "Already at requested stage"

    current_idx = STAGE_ORDER.index(session.current_stage) if session.current_stage in STAGE_ORDER else 0
    target_idx = STAGE_ORDER.index(target_stage) if target_stage in STAGE_ORDER else 0

    if target_idx < current_idx:
        return True, "Moving back to earlier stage permitted"

    if bypass_approval:
        return True, "Approval gate bypassed by explicit user request"

    for prereq in STAGE_PREREQUISITES.get(target_stage, []):
        # Special allowance if the upstream output already exists in the session.
        if prereq == StageEnum.MOM and session.outputs.get("mom"):
            continue
        if prereq == StageEnum.USER_STORY and session.outputs.get("agile_stories"):
            continue
        if prereq == StageEnum.DDL3 and session.outputs.get("ddl3"):
            continue

        if session.approvals.get(prereq.value, {}).get("status") != ApprovalStatus.APPROVED.value:
            return False, f"Cannot advance to stage '{target_stage.value}': Upstream stage '{prereq.value}' output has not been approved."

    return True, "Prerequisites met"
