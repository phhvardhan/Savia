import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.workflow import WorkflowSession, Artifact, StageEnum, ApprovalStatus, TraceabilityLink
from app.core.config import settings
from app.utils.logger import logger


class WorkflowEngine:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        self.workflows_file = os.path.join(self.upload_dir, "workflows.json")
        self.artifacts_file = os.path.join(self.upload_dir, "artifacts.json")
        self._memory_workflows: Dict[str, WorkflowSession] = {}
        self._memory_artifacts: Dict[str, Artifact] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.workflows_file):
            try:
                with open(self.workflows_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for wf_id, wf_dict in data.items():
                        self._memory_workflows[wf_id] = WorkflowSession(**wf_dict)
            except Exception as e:
                logger.warning(f"[WorkflowEngine] Failed loading workflows from disk: {e}")

        if os.path.exists(self.artifacts_file):
            try:
                with open(self.artifacts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for art_id, art_dict in data.items():
                        self._memory_artifacts[art_id] = Artifact(**art_dict)
            except Exception as e:
                logger.warning(f"[WorkflowEngine] Failed loading artifacts from disk: {e}")

    def _save_to_disk(self):
        try:
            with open(self.workflows_file, "w", encoding="utf-8") as f:
                data = {wf_id: wf.dict() for wf_id, wf in self._memory_workflows.items()}
                json.dump(data, f, indent=2)

            with open(self.artifacts_file, "w", encoding="utf-8") as f:
                data = {art_id: art.dict() for art_id, art in self._memory_artifacts.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[WorkflowEngine] Error saving state to disk: {e}")

    def create_workflow(self, title: str = "SAVIA SDLC Session", source_documents: List[Dict[str, Any]] = None, normalized_input: str = "", input_type: str = "unknown") -> WorkflowSession:
        session = WorkflowSession(
            title=title,
            source_documents=source_documents or [],
            normalized_input=normalized_input,
            input_type=input_type,
            current_stage=StageEnum.INGESTION if not normalized_input else StageEnum.REQUIREMENTS,
        )
        session.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "workflow_created",
            "stage": session.current_stage.value,
        })
        self._memory_workflows[session.workflow_id] = session
        self._save_to_disk()
        return session

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowSession]:
        return self._memory_workflows.get(workflow_id)

    def list_workflows(self) -> List[WorkflowSession]:
        return list(self._memory_workflows.values())

    def update_workflow(self, session: WorkflowSession) -> WorkflowSession:
        session.updated_at = datetime.utcnow().isoformat()
        self._memory_workflows[session.workflow_id] = session
        self._save_to_disk()
        return session

    def save_artifact(self, workflow_id: str, agent_name: str, stage: StageEnum, content: Dict[str, Any], traceability: TraceabilityLink = None) -> Artifact:
        session = self.get_workflow(workflow_id)
        version = 1
        if session:
            # Check existing versions
            existing = [a for a in self._memory_artifacts.values() if a.workflow_id == workflow_id and a.agent_name == agent_name]
            version = len(existing) + 1

        artifact = Artifact(
            workflow_id=workflow_id,
            agent_name=agent_name,
            stage=stage,
            version=version,
            content=content,
            traceability=traceability or TraceabilityLink(),
        )

        self._memory_artifacts[artifact.artifact_id] = artifact

        if session:
            output_key = agent_name.replace("-", "_")
            if output_key in session.outputs:
                session.outputs[output_key] = artifact.content
            session.history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "artifact_generated",
                "agent_name": agent_name,
                "artifact_id": artifact.artifact_id,
                "version": version,
            })
            self.update_workflow(session)

        self._save_to_disk()
        return artifact

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return self._memory_artifacts.get(artifact_id)

    def get_workflow_artifacts(self, workflow_id: str) -> List[Artifact]:
        return [a for a in self._memory_artifacts.values() if a.workflow_id == workflow_id]


workflow_engine = WorkflowEngine()
