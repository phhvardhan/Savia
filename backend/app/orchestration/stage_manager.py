from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.workflow import ApprovalStatus, Artifact, StageEnum, WorkflowSession
from app.orchestration.workflow_engine import workflow_engine
from app.utils.logger import logger


class GateError(Exception):
    pass


class StageManager:
    def upstream_for(self, session: WorkflowSession, consumes: Tuple[str, ...]) -> Dict[str, Any]:
        content: Dict[str, Any] = {}
        used: List[str] = []
        skipped: List[str] = []
        latest = workflow_engine.latest_artifacts(session.workflow_id)
        for agent_id in consumes:
            approved = workflow_engine.latest_approved(session.workflow_id, agent_id)
            if approved:
                content[agent_id] = approved.content
                used.append(approved.artifact_id)
            elif agent_id in latest:
                skipped.append(agent_id)
        return {"content": content, "artifact_ids": used, "unapproved": skipped}

    def pending_artifacts(self, session: WorkflowSession) -> List[Artifact]:
        return [
            a for a in workflow_engine.latest_artifacts(session.workflow_id).values()
            if a.approval_status != ApprovalStatus.APPROVED
        ]

    def approve(
        self,
        session: WorkflowSession,
        artifact: Optional[Artifact],
        user_id: str,
        comments: Optional[str] = None,
        status: ApprovalStatus = ApprovalStatus.APPROVED,
    ) -> Artifact:
        if artifact is None:
            raise GateError("There is no output in this workflow to approve yet.")
        if artifact.workflow_id != session.workflow_id:
            raise GateError("That output belongs to another workflow.")
        now = datetime.utcnow().isoformat()
        artifact.approval_status = status
        artifact.approved_by = user_id
        artifact.approved_at = now
        artifact.approval_comments = comments
        workflow_engine.update_artifact(artifact)
        session.approvals[artifact.artifact_id] = {
            "status": status.value,
            "agent_name": artifact.agent_name,
            "version": artifact.version,
            "approved_by": user_id,
            "approved_at": now,
            "comments": comments,
        }
        session.log(f"artifact_{status.value}", artifact_id=artifact.artifact_id, agent_name=artifact.agent_name,
                    version=artifact.version, by=user_id)
        session.status = "waiting_for_approval" if self.pending_artifacts(session) else "approved"
        workflow_engine.update_workflow(session)
        logger.info(f"[StageManager] {artifact.artifact_id} {status.value} by {user_id}")
        return artifact

    def move_to(self, session: WorkflowSession, stage: StageEnum, require_approved: bool = False) -> WorkflowSession:
        if require_approved:
            pending = self.pending_artifacts(session)
            if pending:
                names = ", ".join(f"{a.agent_name} v{a.version}" for a in pending)
                raise GateError(f"Approve these outputs before moving on: {names}.")
        if session.current_stage != stage:
            session.log("stage_advanced", from_stage=session.current_stage.value, to_stage=stage.value)
            session.current_stage = stage
        return session


stage_manager = StageManager()
