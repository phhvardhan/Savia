from fastapi import HTTPException, status

from app.services.run_service import RunService
from app.schemas.entities.run_entity import Run, RunStep
from app.utils.response import success_response, error_response


run_service = RunService()


class RunController:

    async def get_run(self, run_id: str) -> Run:
        return run_service.get_run(run_id)

    async def get_steps(self, run_id: str) -> list[RunStep]:
        return run_service.get_steps(run_id)

    async def cancel_run(self, run_id: str) -> Run:
        return run_service.cancel_run(run_id)
