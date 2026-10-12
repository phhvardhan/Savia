from typing import Tuple, Optional
from datetime import datetime
from app.models.workflow import WorkflowSession, StageEnum, ApprovalStatus
from app.orchestration.workflow_engine import workflow_engine
from app.utils.logger import logger


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


class StageManager:
    def can_advance(self, session: WorkflowSession, target_stage: StageEnum, bypass_approval: bool = False) -> Tuple[bool, str]:
        if session.current_stage == target_stage:
            return True, "Already at requested stage"

        current_idx = STAGE_ORDER.index(session.current_stage) if session.current_stage in STAGE_ORDER else 0
        target_idx = STAGE_ORDER.index(target_stage) if target_stage in STAGE_ORDER else 0

        if target_idx < current_idx:
            return True, "Moving back to earlier stage permitted"

        if bypass_approval:
            return True, "Approval gate bypassed by explicit user request"

        # Check approval prerequisite
        prereqs = STAGE_PREREQUISITES.get(target_stage, [])
        for prereq in prereqs:
            prereq_key = prereq.value
            approval_record = session.approvals.get(prereq_key, {})
            status = approval_record.get("status")
            
            # Special allowance if MOM or requirements exist in session output
            if prereq == StageEnum.MOM and session.outputs.get("mom"):
                continue
            if prereq == StageEnum.USER_STORY and session.outputs.get("user_stories"):
                continue
            if prereq == StageEnum.DDL3 and session.outputs.get("ddl3"):
                continue

            if status != ApprovalStatus.APPROVED.value:
                return False, f"Cannot advance to stage '{target_stage.value}': Upstream stage '{prereq_key}' output has not been approved."

        return True, "Prerequisites met"

    def approve_stage(self, session: WorkflowSession, stage: StageEnum, user_id: str = "system_user", comments: str = None) -> WorkflowSession:
        stage_key = stage.value
        session.approvals[stage_key] = {
            "status": ApprovalStatus.APPROVED.value,
            "approved_by": user_id,
            "approved_at": datetime.utcnow().isoformat(),
            "comments": comments or "Approved",
        }

        session.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "stage_approved",
            "stage": stage_key,
            "approved_by": user_id,
        })

        logger.info(f"[StageManager] Stage '{stage_key}' approved for workflow '{session.workflow_id}' by user '{user_id}'")
        return workflow_engine.update_workflow(session)

    def advance_stage(self, session: WorkflowSession, target_stage: StageEnum, bypass_approval: bool = False) -> Tuple[bool, str, WorkflowSession]:
        allowed, reason = self.can_advance(session, target_stage, bypass_approval=bypass_approval)
        if not allowed:
            return False, reason, session

        previous_stage = session.current_stage
        session.current_stage = target_stage
        session.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "stage_advanced",
            "from_stage": previous_stage.value,
            "to_stage": target_stage.value,
        })
        updated = workflow_engine.update_workflow(session)
        logger.info(f"[StageManager] Workflow '{session.workflow_id}' advanced from '{previous_stage.value}' to '{target_stage.value}'")
        return True, f"Advanced to stage '{target_stage.value}'", updated


stage_manager = StageManager()
