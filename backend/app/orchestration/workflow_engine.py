import os
import json
from typing import Optional, Dict, List
from app.models.workflow import WorkflowSession, Artifact
from app.core.config import settings
from app.utils.logger import logger


class WorkflowEngine:
    """
    Read model for the API: sessions and artifacts as JSON files.
    SdlcWorkflow (Temporal) owns the state and is the only writer, through the
    `persist` activity. The API process just reads, reloading when a file changes.
    """

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        self.workflows_file = os.path.join(self.upload_dir, "workflows.json")
        self.artifacts_file = os.path.join(self.upload_dir, "artifacts.json")
        self._memory_workflows: Dict[str, WorkflowSession] = {}
        self._memory_artifacts: Dict[str, Artifact] = {}
        self._mtimes: Dict[str, float] = {}

    def _refresh(self):
        for path, store, model in (
            (self.workflows_file, self._memory_workflows, WorkflowSession),
            (self.artifacts_file, self._memory_artifacts, Artifact),
        ):
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            if self._mtimes.get(path) == mtime:
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                store.update({key: model(**value) for key, value in data.items()})
                self._mtimes[path] = mtime
            except Exception as e:
                logger.warning(f"[WorkflowEngine] Failed loading {path}: {e}")

    def _save(self, path: str, store: dict):
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({key: value.model_dump(mode="json") for key, value in store.items()}, f, indent=2)
        os.replace(tmp, path)  # readers in the API process never see a half-written file
        self._mtimes[path] = os.path.getmtime(path)

    # ponytail: whole-file rewrite, one worker process. Swap for a database if the worker scales out.
    def put_session(self, session: WorkflowSession) -> None:
        self._refresh()
        self._memory_workflows[session.workflow_id] = session
        self._save(self.workflows_file, self._memory_workflows)

    def put_artifact(self, artifact: Artifact) -> None:
        self._refresh()
        self._memory_artifacts[artifact.artifact_id] = artifact
        self._save(self.artifacts_file, self._memory_artifacts)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowSession]:
        self._refresh()
        return self._memory_workflows.get(workflow_id)

    def list_workflows(self) -> List[WorkflowSession]:
        self._refresh()
        return list(self._memory_workflows.values())

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        self._refresh()
        return self._memory_artifacts.get(artifact_id)

    def get_workflow_artifacts(self, workflow_id: str) -> List[Artifact]:
        self._refresh()
        return [a for a in self._memory_artifacts.values() if a.workflow_id == workflow_id]


workflow_engine = WorkflowEngine()
