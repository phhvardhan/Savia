import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.db import db
from app.core.llm import current_purpose, current_run_id
from app.core.quality import assess, traceability
from app.models.workflow import Artifact, WorkflowSession
from app.orchestration.handoff import readiness
from app.orchestration.stage_manager import stage_manager
from app.orchestration.workflow_engine import workflow_engine
from app.utils.logger import logger


def _now() -> str:
    return datetime.utcnow().isoformat()


def artifact_response(artifact: Artifact, upstream: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "workflow_id": artifact.workflow_id,
        "artifact_id": artifact.artifact_id,
        "agent_name": artifact.agent_name,
        "stage": artifact.stage.value,
        "version": artifact.version,
        "content": artifact.content,
        "quality": artifact.quality,
        "approval_status": artifact.approval_status.value,
        "upstream_used": (upstream or {}).get("artifact_ids", []),
        "upstream_unapproved": (upstream or {}).get("unapproved", []),
        "readiness": artifact.meta.get("readiness"),
        "run_id": run_id,
    }


class AgentRunner:
    def __init__(self):
        self._tasks: set[asyncio.Task] = set()
        self._gate: Optional[asyncio.Semaphore] = None
        self._gate_loop: Optional[asyncio.AbstractEventLoop] = None
        db.execute(
            "UPDATE runs SET status = 'failed', error = 'Interrupted by a server restart.', finished_at = ?"
            " WHERE status IN ('queued', 'running')",
            (_now(),),
        )

    def _semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._gate is None or self._gate_loop is not loop:
            self._gate = asyncio.Semaphore(settings.MAX_CONCURRENT_RUNS)
            self._gate_loop = loop
        return self._gate

    async def execute(
        self,
        agent: BaseAgent,
        session: WorkflowSession,
        input_text: str,
        options: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        upstream = stage_manager.upstream_for(session, agent.consumes)
        run_token = current_run_id.set(run_id)
        purpose_token = current_purpose.set(agent.id)
        try:
            async with self._semaphore():
                # One rubric for every run: a draft that is not ready gets one revision with the reviewer's notes.
                attempt_text, best = input_text, None
                for attempt in (1, 2):
                    input_data = {"text": attempt_text, "normalized_input": attempt_text, "upstream": upstream["content"], **(options or {})}
                    content = await agent.run(input_data)
                    quality = assess(content, input_text, upstream["content"], agent.defines)
                    verdict = readiness(agent, content, quality, input_text, upstream["content"])
                    verdict["attempts"] = attempt
                    if best is None or verdict["score"] >= best[2]["score"]:
                        best = (content, quality, verdict)
                    if verdict["ready"] or attempt == 2:
                        break
                    logger.info(f"[Runner] {agent.id} draft not ready ({verdict['issues']}); revising once")
                    attempt_text = (
                        f"{input_text}\n\nREVIEWER NOTES ON THE PREVIOUS DRAFT (fix these; never mention this note):\n- "
                        + "\n- ".join(verdict["issues"])
                    )
                content, quality, verdict = best
        finally:
            current_run_id.reset(run_token)
            current_purpose.reset(purpose_token)

        artifact = workflow_engine.save_artifact(
            workflow_id=session.workflow_id,
            agent_name=agent.id,
            stage=agent.stage,
            content=content,
            traceability=traceability(content, input_text, upstream["artifact_ids"], session.workflow_id),
            quality=quality,
            meta={
                "prompt_version": agent.prompt_version,
                "run_id": run_id,
                "upstream_used": upstream["artifact_ids"],
                "upstream_unapproved": upstream["unapproved"],
                "readiness": verdict,
                "handoff_from": (options or {}).get("handoff_from"),
            },
        )
        fresh = workflow_engine.get_workflow(session.workflow_id) or session
        stage_manager.move_to(fresh, agent.stage)
        fresh.status = "waiting_for_approval"
        workflow_engine.update_workflow(fresh)
        return artifact_response(artifact, upstream, run_id)

    @staticmethod
    def _hash(agent_id: str, workflow_id: str, input_text: str, options: Dict[str, Any]) -> str:
        key = f"{agent_id}|{workflow_id}|{sorted(options.items())}|{input_text}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def submit(
        self, agent: BaseAgent, session: WorkflowSession, input_text: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        options = options or {}
        input_hash = self._hash(agent.id, session.workflow_id, input_text, options)
        existing = db.query(
            "SELECT id FROM runs WHERE input_hash = ? AND status IN ('queued', 'running')", (input_hash,)
        )
        if existing:
            return self.get(existing[0]["id"])
        run_id = f"run-{uuid.uuid4().hex[:10]}"
        db.execute(
            "INSERT INTO runs (id, workflow_id, agent_id, status, input_hash, created_at) VALUES (?, ?, ?, 'queued', ?, ?)",
            (run_id, session.workflow_id, agent.id, input_hash, _now()),
        )
        task = asyncio.create_task(self._work(run_id, agent, session, input_text, options))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return self.get(run_id)

    async def _work(self, run_id: str, agent: BaseAgent, session: WorkflowSession, input_text: str, options: Dict[str, Any]):
        db.execute("UPDATE runs SET status = 'running', started_at = ? WHERE id = ?", (_now(), run_id))
        try:
            result = await self.execute(agent, session, input_text, options, run_id)
        except Exception as e:
            logger.exception(f"[Runner] {run_id} ({agent.id}) failed")
            db.execute(
                "UPDATE runs SET status = 'failed', error = ?, finished_at = ? WHERE id = ?",
                (str(e)[:1000] or type(e).__name__, _now(), run_id),
            )
            return
        db.execute(
            "UPDATE runs SET status = 'done', artifact_id = ?, finished_at = ? WHERE id = ?",
            (result["artifact_id"], _now(), run_id),
        )

    def get(self, run_id: str) -> Optional[Dict[str, Any]]:
        rows = db.query("SELECT * FROM runs WHERE id = ?", (run_id,))
        if not rows:
            return None
        run = dict(rows[0])
        run.pop("input_hash", None)
        usage = db.query(
            "SELECT COUNT(*) AS calls, COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,"
            " COALESCE(SUM(completion_tokens), 0) AS completion_tokens FROM llm_calls WHERE run_id = ?",
            (run_id,),
        )[0]
        run["usage"] = dict(usage)
        if run["status"] == "done" and run["artifact_id"]:
            artifact = workflow_engine.get_artifact(run["artifact_id"])
            if artifact:
                run["result"] = artifact_response(
                    artifact,
                    {"artifact_ids": artifact.meta.get("upstream_used", []),
                     "unapproved": artifact.meta.get("upstream_unapproved", [])},
                    run_id,
                )
        return run


agent_runner = AgentRunner()
