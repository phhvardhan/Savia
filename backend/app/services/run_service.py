

from datetime import datetime
from typing import Callable, List, Optional

from fastapi import HTTPException, status

from app.core.repositories import run_repo, run_step_repo
from app.schemas.entities.run_entity import (
    Run, RunStep, RunType, RunStatus, RunStepStatus,
)


class RunService:

    def start_run(
        self,
        run_type: RunType,
        workspace_id: str,
        source_type: str,
        source_id: str,
        created_by: str,
        step_names: List[str],
        template_id: Optional[str] = None,
    ) -> Run:
        run = run_repo.add(Run(
            type=run_type,
            workspace_id=workspace_id,
            source_type=source_type,
            source_id=source_id,
            template_id=template_id,
            status=RunStatus.PROCESSING,
            started_at=datetime.utcnow().isoformat(),
            created_by=created_by,
        ))

        step_ids = []
        for i, name in enumerate(step_names):
            step = run_step_repo.add(RunStep(run_id=run.id, order=i, name=name))
            step_ids.append(step.id)

        return run_repo.update(run.id, steps=step_ids)

    def execute_step(self, run_id: str, step_order: int, work_fn: Callable[[], None]) -> None:
        """
        Marks a step processing -> runs work_fn() -> marks it completed.
        work_fn does the actual (currently mocked) content generation and
        is responsible for persisting whatever entity it produces
        (summary, stories, document sections, ...) via its own repo.
        """
        steps = run_step_repo.list(filter_fn=lambda s: s.run_id == run_id and s.order == step_order)
        if not steps:
            return
        step = steps[0]

        run_step_repo.update(step.id, status=RunStepStatus.PROCESSING, started_at=datetime.utcnow().isoformat())
        work_fn()
        run_step_repo.update(step.id, status=RunStepStatus.COMPLETED, completed_at=datetime.utcnow().isoformat())

        total_steps = len(run_repo.get(run_id).steps)
        progress = int(((step_order + 1) / total_steps) * 100)
        run_repo.update(
            run_id,
            overall_progress_percent=progress,
            current_step_name=step.name,
        )

    def complete_run(self, run_id: str) -> Run:
        return run_repo.update(
            run_id,
            status=RunStatus.COMPLETED,
            overall_progress_percent=100,
            completed_at=datetime.utcnow().isoformat(),
        )

    def fail_run(self, run_id: str, error_message: str) -> Run:
        return run_repo.update(run_id, status=RunStatus.FAILED, error_message=error_message)

    def get_run(self, run_id: str) -> Run:
        run = run_repo.get(run_id)
        if not run:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found")
        return run

    def get_steps(self, run_id: str) -> List[RunStep]:
        steps = run_step_repo.list(filter_fn=lambda s: s.run_id == run_id)
        return sorted(steps, key=lambda s: s.order)

    def cancel_run(self, run_id: str) -> Run:
        run = self.get_run(run_id)
        if run.status != RunStatus.PROCESSING:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only a processing run can be cancelled")
        return run_repo.update(run_id, status=RunStatus.CANCELLED)
