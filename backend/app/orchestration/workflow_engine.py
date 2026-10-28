import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.db import db
from app.models.workflow import ApprovalStatus, Artifact, StageEnum, TraceabilityLink, WorkflowSession
from app.utils.logger import logger


def _now() -> str:
    return datetime.utcnow().isoformat()


class WorkflowEngine:
    def __init__(self):
        self._import_legacy_json()

    def _import_legacy_json(self) -> None:
        if db.query("SELECT 1 FROM workflows LIMIT 1"):
            return
        workflows_file = os.path.join(settings.UPLOAD_DIR, "workflows.json")
        artifacts_file = os.path.join(settings.UPLOAD_DIR, "artifacts.json")
        try:
            with db.transaction() as conn:
                if os.path.exists(workflows_file):
                    with open(workflows_file, "r", encoding="utf-8") as f:
                        for wf in json.load(f).values():
                            self._write_workflow(conn, WorkflowSession(**wf))
                if os.path.exists(artifacts_file):
                    with open(artifacts_file, "r", encoding="utf-8") as f:
                        for art in json.load(f).values():
                            artifact = Artifact(**art)
                            conn.execute(
                                "INSERT OR IGNORE INTO artifacts (id, workflow_id, agent_name, version, data, created_at)"
                                " VALUES (?, ?, ?, ?, ?, ?)",
                                (artifact.artifact_id, artifact.workflow_id, artifact.agent_name, artifact.version,
                                 artifact.model_dump_json(), artifact.created_at),
                            )
        except Exception as e:
            logger.warning(f"[WorkflowEngine] Legacy JSON import skipped: {e}")

    @staticmethod
    def _write_workflow(conn, session: WorkflowSession) -> None:
        conn.execute(
            "INSERT INTO workflows (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at",
            (session.workflow_id, session.model_dump_json(), session.created_at, session.updated_at),
        )

    @staticmethod
    def _read_workflow(conn, workflow_id: str) -> Optional[WorkflowSession]:
        row = conn.execute("SELECT data FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        return WorkflowSession.model_validate_json(row["data"]) if row else None

    def create_workflow(
        self,
        title: str = "SAVIA SDLC Session",
        source_documents: Optional[List[Dict[str, Any]]] = None,
        normalized_input: str = "",
        input_type: str = "unknown",
    ) -> WorkflowSession:
        session = WorkflowSession(
            title=title,
            source_documents=source_documents or [],
            normalized_input=normalized_input,
            input_type=input_type,
            current_stage=StageEnum.REQUIREMENTS if normalized_input else StageEnum.INGESTION,
        )
        session.log("workflow_created", stage=session.current_stage.value)
        with db.transaction() as conn:
            self._write_workflow(conn, session)
        return session

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowSession]:
        rows = db.query("SELECT data FROM workflows WHERE id = ?", (workflow_id,))
        return WorkflowSession.model_validate_json(rows[0]["data"]) if rows else None

    def list_workflows(self) -> List[WorkflowSession]:
        rows = db.query("SELECT data FROM workflows ORDER BY updated_at DESC")
        return [WorkflowSession.model_validate_json(r["data"]) for r in rows]

    def update_workflow(self, session: WorkflowSession) -> WorkflowSession:
        session.updated_at = _now()
        with db.transaction() as conn:
            self._write_workflow(conn, session)
        return session

    def save_artifact(
        self,
        workflow_id: str,
        agent_name: str,
        stage: StageEnum,
        content: Dict[str, Any],
        traceability: Optional[TraceabilityLink] = None,
        quality: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        with db.transaction() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS v FROM artifacts WHERE workflow_id = ? AND agent_name = ?",
                (workflow_id, agent_name),
            ).fetchone()
            artifact = Artifact(
                workflow_id=workflow_id,
                agent_name=agent_name,
                stage=stage,
                version=row["v"] + 1,
                content=content,
                traceability=traceability or TraceabilityLink(),
                quality=quality or {},
                meta=meta or {},
            )
            conn.execute(
                "INSERT INTO artifacts (id, workflow_id, agent_name, version, data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (artifact.artifact_id, workflow_id, agent_name, artifact.version, artifact.model_dump_json(),
                 artifact.created_at),
            )
            session = self._read_workflow(conn, workflow_id)
            if session:
                session.outputs[agent_name] = content
                session.log("artifact_generated", agent_name=agent_name, artifact_id=artifact.artifact_id,
                            version=artifact.version)
                session.updated_at = _now()
                self._write_workflow(conn, session)
        return artifact

    def update_artifact(self, artifact: Artifact) -> Artifact:
        db.execute("UPDATE artifacts SET data = ? WHERE id = ?", (artifact.model_dump_json(), artifact.artifact_id))
        return artifact

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        rows = db.query("SELECT data FROM artifacts WHERE id = ?", (artifact_id,))
        return Artifact.model_validate_json(rows[0]["data"]) if rows else None

    def get_workflow_artifacts(self, workflow_id: str) -> List[Artifact]:
        rows = db.query(
            "SELECT data FROM artifacts WHERE workflow_id = ? ORDER BY agent_name, version", (workflow_id,)
        )
        return [Artifact.model_validate_json(r["data"]) for r in rows]

    def latest_artifacts(self, workflow_id: str) -> Dict[str, Artifact]:
        latest: Dict[str, Artifact] = {}
        for artifact in self.get_workflow_artifacts(workflow_id):
            latest[artifact.agent_name] = artifact
        return latest

    def latest_approved(self, workflow_id: str, agent_name: str) -> Optional[Artifact]:
        approved = [
            a for a in self.get_workflow_artifacts(workflow_id)
            if a.agent_name == agent_name and a.approval_status == ApprovalStatus.APPROVED
        ]
        return approved[-1] if approved else None


workflow_engine = WorkflowEngine()
