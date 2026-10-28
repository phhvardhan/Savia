"""Temporal worker: runs SdlcWorkflow and its activities. Start with `python -m app.worker`."""
import asyncio
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker
from app.core.config import settings
from app.orchestration.activities import persist, recommend, run_agent
from app.orchestration.workflows import SdlcWorkflow
from app.utils.logger import logger


async def main() -> None:
    client = await Client.connect(
        settings.TEMPORAL_ADDRESS, namespace=settings.TEMPORAL_NAMESPACE, data_converter=pydantic_data_converter,
    )
    logger.info(f"[Worker] {settings.TEMPORAL_ADDRESS} queue={settings.TEMPORAL_TASK_QUEUE}")
    await Worker(
        client, task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[SdlcWorkflow], activities=[recommend, run_agent, persist],
    ).run()


if __name__ == "__main__":
    asyncio.run(main())
