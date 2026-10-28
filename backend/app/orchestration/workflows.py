import asyncio
from datetime import timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from app.agents import AGENT_MAP
    from app.models.workflow import (
        Artifact, ApprovalStatus, StageEnum, TraceabilityLink, WorkflowSession,
    )
    from app.orchestration.activities import PersistInput, RecommendInput, persist, recommend, run_agent
    from app.orchestration.stage_manager import can_advance

# Maps an agent id to the key it fills in session.outputs (the rest of the app reads these keys).
AGENT_OUTPUT_KEY = {"agile-stories": "agile_stories", "test": "tests"}

LLM_TIMEOUT = timedelta(minutes=5)
LLM_RETRY = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=2), backoff_coefficient=2.0)


class RecommendRequest(BaseModel):
    raw_text: Optional[str] = None
    input_type: Optional[str] = None
    filename: Optional[str] = None


class RunAgentRequest(BaseModel):
    agent_id: str
    input_text: str = ""
    document_type: str = "functional_design"
    bypass_approval: bool = False


class ApproveRequest(BaseModel):
    user_id: str = "system_user"
    comments: str = "Approved"


class AdvanceRequest(BaseModel):
    target_stage: StageEnum
    bypass_approval: bool = False


class SaveArtifactRequest(BaseModel):
    agent_name: str
    stage: StageEnum
    content: Dict[str, Any]
    traceability: TraceabilityLink


def _reject(reason: str):
    raise ApplicationError(reason, type="Rejected", non_retryable=True)


@workflow.defn
class SdlcWorkflow:
    """
    One SAVIA session. Holds the session and its artifacts, enforces the approval
    gates, and runs every LLM call as a retried activity. Mutating updates are
    serialised by a lock so two clicks can't interleave.
    """

    def __init__(self) -> None:
        self.session: Optional[WorkflowSession] = None
        self.artifacts: List[Artifact] = []
        self._lock = asyncio.Lock()
        self._ready = False

    @workflow.run
    async def run(self, session: WorkflowSession) -> None:
        self.session = session
        await self._persist()
        self._ready = True
        # Sessions are long-lived and the user may step back from COMPLETED, so close it in the Temporal UI.
        await workflow.wait_condition(lambda: False)

    # -- helpers ---------------------------------------------------------

    def _log(self, event: str, **fields) -> None:
        self.session.history.append({"timestamp": workflow.now().isoformat(), "event": event, **fields})

    async def _persist(self, artifact: Optional[Artifact] = None) -> None:
        self.session.updated_at = workflow.now().isoformat()
        await workflow.execute_activity(
            persist, PersistInput(session=self.session, artifact=artifact),
            start_to_close_timeout=timedelta(seconds=30), retry_policy=RetryPolicy(maximum_attempts=5),
        )

    def _new_artifact(self, agent_name: str, stage: StageEnum, content: Dict[str, Any], traceability: TraceabilityLink) -> Artifact:
        version = sum(a.agent_name == agent_name for a in self.artifacts) + 1
        artifact = Artifact(
            artifact_id=f"art-{workflow.uuid4().hex[:8]}",
            workflow_id=self.session.workflow_id,
            agent_name=agent_name,
            stage=stage,
            version=version,
            content=content,
            traceability=traceability,
            created_at=workflow.now().isoformat(),
        )
        self.artifacts.append(artifact)
        output_key = AGENT_OUTPUT_KEY.get(agent_name, agent_name.replace("-", "_"))
        if output_key in self.session.outputs:
            self.session.outputs[output_key] = content
        self._log("artifact_generated", agent_name=agent_name, artifact_id=artifact.artifact_id, version=version)
        return artifact

    def _move_to(self, target: StageEnum) -> None:
        previous = self.session.current_stage
        if previous != target:
            self.session.current_stage = target
            self._log("stage_advanced", from_stage=previous.value, to_stage=target.value)

    # -- updates and queries ---------------------------------------------

    @workflow.update
    async def ready(self) -> WorkflowSession:
        """Returns once the session is in the read model, so a caller can read it straight after create."""
        await workflow.wait_condition(lambda: self._ready)
        return self.session

    @workflow.query
    def state(self) -> WorkflowSession:
        return self.session

    @workflow.update
    async def recommend_agents(self, req: RecommendRequest) -> Dict[str, Any]:
        await workflow.wait_condition(lambda: self._ready)
        return await workflow.execute_activity(
            recommend, RecommendInput(session=self.session, **req.model_dump()),
            start_to_close_timeout=LLM_TIMEOUT, retry_policy=LLM_RETRY,
        )

    @workflow.update
    async def approve(self, req: ApproveRequest) -> WorkflowSession:
        async with self._lock:
            stage = self.session.current_stage.value
            self.session.approvals[stage] = {
                "status": ApprovalStatus.APPROVED.value,
                "approved_by": req.user_id,
                "approved_at": workflow.now().isoformat(),
                "comments": req.comments,
            }
            self._log("stage_approved", stage=stage, approved_by=req.user_id)
            await self._persist()
            return self.session

    @workflow.update
    async def advance(self, req: AdvanceRequest) -> WorkflowSession:
        async with self._lock:
            allowed, reason = can_advance(self.session, req.target_stage, req.bypass_approval)
            if not allowed:  # re-checked under the lock: an earlier update may have changed the gates
                _reject(reason)
            self._move_to(req.target_stage)
            await self._persist()
            return self.session

    @advance.validator
    def _validate_advance(self, req: AdvanceRequest) -> None:
        allowed, reason = can_advance(self.session, req.target_stage, req.bypass_approval)
        if not allowed:
            _reject(reason)

    @workflow.update
    async def run_agent_step(self, req: RunAgentRequest) -> Artifact:
        async with self._lock:
            agent = AGENT_MAP[req.agent_id]
            allowed, reason = can_advance(self.session, agent.stage, req.bypass_approval)
            if not allowed:
                _reject(reason)
            text = req.input_text or self.session.normalized_input
            outputs = self.session.outputs
            content = await workflow.execute_activity(
                run_agent,
                args=[req.agent_id, {
                    "text": text, "normalized_input": text, "document_type": req.document_type,
                    "mom": outputs.get("mom"), "agile_stories": outputs.get("agile_stories"),
                    "ddl3": outputs.get("ddl3"), "outputs": outputs,
                }],
                start_to_close_timeout=LLM_TIMEOUT, retry_policy=LLM_RETRY,
            )
            stage = agent.stage
            artifact = self._new_artifact(req.agent_id, stage, content, TraceabilityLink(
                requirement_id=self.session.workflow_id,
                user_story_id="US-001" if stage != StageEnum.MOM else None,
                design_id="DES-001" if stage in (StageEnum.DDL3, StageEnum.TESTING) else None,
                test_case_id="TC-001" if stage == StageEnum.TESTING else None,
                source_reference=self.session.workflow_id,
            ))
            self._move_to(stage)  # running an agent moves the session to its stage, as it always has
            await self._persist(artifact)
            return artifact

    @run_agent_step.validator
    def _validate_run_agent(self, req: RunAgentRequest) -> None:
        agent = AGENT_MAP.get(req.agent_id)
        if not agent:
            _reject(f"Agent '{req.agent_id}' not found.")
        allowed, reason = can_advance(self.session, agent.stage, req.bypass_approval)
        if not allowed:
            _reject(reason)
        if not (req.input_text or self.session.normalized_input):
            _reject("Either workflow_id or input_text must be provided.")

    @workflow.update
    async def save_artifact_version(self, req: SaveArtifactRequest) -> Artifact:
        """A user edit: new version of an existing agent's output; earlier versions stay."""
        async with self._lock:
            artifact = self._new_artifact(req.agent_name, req.stage, req.content, req.traceability)
            await self._persist(artifact)
            return artifact
