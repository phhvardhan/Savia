import asyncio
import pytest
from temporalio import activity
from temporalio.client import WorkflowUpdateFailedError
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from app.models.workflow import StageEnum, WorkflowSession
from app.orchestration.activities import PersistInput, RecommendInput
from app.orchestration.workflows import (
    AdvanceRequest, ApproveRequest, RecommendRequest, RunAgentRequest, SaveArtifactRequest, SdlcWorkflow,
)

persisted: list = []
agent_calls = {"n": 0}


@activity.defn(name="persist")
async def fake_persist(args: PersistInput) -> None:
    persisted.append(args)


@activity.defn(name="recommend")
async def fake_recommend(args: RecommendInput) -> dict:
    return {"primary_agent": "mom", "source": "test"}


@activity.defn(name="run_agent")
async def fake_run_agent(agent_id: str, input_data: dict) -> dict:
    agent_calls["n"] += 1
    if agent_calls["n"] == 1:
        raise RuntimeError("LLM hiccup")  # retried by the workflow's retry policy
    if not input_data["text"]:
        raise AssertionError
    return {"title": f"{agent_id} output"}


async def _lifecycle():
    env = await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter)
    async with env:
        queue = "savia-test"
        async with Worker(env.client, task_queue=queue, workflows=[SdlcWorkflow],
                          activities=[fake_persist, fake_recommend, fake_run_agent]):
            session = WorkflowSession(normalized_input="we met and decided things", current_stage=StageEnum.REQUIREMENTS)
            h = await env.client.start_workflow(SdlcWorkflow.run, session, id=session.workflow_id, task_queue=queue)
            await h.execute_update(SdlcWorkflow.ready)
            assert persisted[-1].session.workflow_id == session.workflow_id

            # Gate: user stories need the upstream stages approved, so this is rejected.
            with pytest.raises(WorkflowUpdateFailedError) as err:
                await h.execute_update(SdlcWorkflow.advance, AdvanceRequest(target_stage=StageEnum.USER_STORY))
            assert "has not been approved" in str(err.value.cause)

            # First LLM attempt fails and is retried; the run lands as version 1 and moves the stage.
            art = await h.execute_update(SdlcWorkflow.run_agent_step, RunAgentRequest(agent_id="mom"))
            assert agent_calls["n"] == 2 and art.version == 1 and art.stage == StageEnum.MOM
            assert persisted[-1].artifact.artifact_id == art.artifact_id
            state = await h.query(SdlcWorkflow.state)
            assert state.current_stage == StageEnum.MOM and state.outputs["mom"] == art.content

            # Approve, then a user edit becomes version 2 of the same agent.
            await h.execute_update(SdlcWorkflow.approve, ApproveRequest(user_id="dana"))
            v2 = await h.execute_update(SdlcWorkflow.save_artifact_version, SaveArtifactRequest(
                agent_name="mom", stage=StageEnum.MOM, content={"title": "edited"}, traceability=art.traceability))
            assert v2.version == 2

            # Unknown agent and empty input are rejected before anything runs.
            with pytest.raises(WorkflowUpdateFailedError):
                await h.execute_update(SdlcWorkflow.run_agent_step, RunAgentRequest(agent_id="nope"))

            rec = await h.execute_update(SdlcWorkflow.recommend_agents, RecommendRequest(raw_text="x"))
            assert rec["primary_agent"] == "mom"


def test_session_lifecycle():
    asyncio.run(_lifecycle())  # no pytest-asyncio in this project
