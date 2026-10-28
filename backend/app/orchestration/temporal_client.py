from typing import Any, Awaitable, Callable, Optional
from fastapi import HTTPException
from temporalio.client import Client, WorkflowUpdateFailedError
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import ApplicationError
from temporalio.service import RPCError, RPCStatusCode
from app.core.config import settings
from app.models.workflow import WorkflowSession
from app.orchestration.workflows import SdlcWorkflow

_client: Optional[Client] = None


async def get_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(
            settings.TEMPORAL_ADDRESS, namespace=settings.TEMPORAL_NAMESPACE,
            data_converter=pydantic_data_converter,
        )
    return _client


async def start_session(title: str, source_documents: list, normalized_input: str, input_type: str) -> WorkflowSession:
    """Starts a SdlcWorkflow and returns once its session is readable from the store."""
    session = WorkflowSession(
        title=title, source_documents=source_documents, normalized_input=normalized_input, input_type=input_type,
        current_stage="requirements" if normalized_input else "ingestion",
    )
    session.history.append({
        "timestamp": session.created_at, "event": "workflow_created", "stage": session.current_stage.value,
    })
    handle = await _call(lambda c: c.start_workflow(
        SdlcWorkflow.run, session, id=session.workflow_id, task_queue=settings.TEMPORAL_TASK_QUEUE,
    ))
    await _call(lambda _: handle.execute_update(SdlcWorkflow.ready))
    return session


async def update(workflow_id: str, update_fn: Callable, arg: Any = None) -> Any:
    """Runs an update on a session's workflow, turning Temporal failures into HTTP errors."""
    return await _call(lambda c: c.get_workflow_handle(workflow_id).execute_update(update_fn, arg))


async def _call(fn: Callable[[Client], Awaitable[Any]]) -> Any:
    try:
        return await fn(await get_client())
    except WorkflowUpdateFailedError as e:
        cause = e
        while cause.__cause__ is not None:  # unwrap ActivityError -> ApplicationError
            cause = cause.__cause__
        status = 400 if isinstance(cause, ApplicationError) and cause.type in ("Rejected", "ValueError") else 500
        raise HTTPException(status_code=status, detail=str(cause))
    except RPCError as e:
        if e.status == RPCStatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Workflow not found.")
        raise HTTPException(status_code=503, detail=f"Temporal error: {e.message}")
    except RuntimeError as e:  # Client.connect failure
        raise HTTPException(status_code=503, detail=f"Temporal is not reachable at {settings.TEMPORAL_ADDRESS}: {e}")
