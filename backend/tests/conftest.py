import asyncio
import threading
import pytest
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from app.core.config import settings
from app.orchestration import temporal_client
from app.orchestration.activities import persist, recommend, run_agent
from app.orchestration.workflows import SdlcWorkflow


@pytest.fixture(scope="session")
def temporal():
    """A real Temporal test server plus our worker, so route tests run the actual workflow."""
    loop = asyncio.new_event_loop()
    ready, stop = threading.Event(), asyncio.Event()
    info = {}

    async def serve():
        async with await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter) as env:
            async with Worker(env.client, task_queue=settings.TEMPORAL_TASK_QUEUE, workflows=[SdlcWorkflow],
                              activities=[recommend, run_agent, persist]):
                info["address"] = env.client.service_client.config.target_host
                ready.set()
                await stop.wait()

    thread = threading.Thread(target=lambda: loop.run_until_complete(serve()), daemon=True)
    thread.start()
    assert ready.wait(60), "Temporal test server did not start"

    # TestClient serves each request on its own event loop, and a Temporal client is bound to one loop.
    async def fresh_client() -> Client:
        return await Client.connect(info["address"], data_converter=pydantic_data_converter)

    original = temporal_client.get_client
    temporal_client.get_client = fresh_client
    yield
    temporal_client.get_client = original
    loop.call_soon_threadsafe(stop.set)
    thread.join(10)
