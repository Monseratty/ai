from __future__ import annotations

from typing import Any

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.api.deps import get_composition_root
from ai_orchestrator.infrastructure.composition import CompositionRoot
from ai_orchestrator.infrastructure.queue.tasks import parse_task_id

celery_app = None


def create_orchestrator_for_worker() -> OrchestratorService:
    raise RuntimeError(
        "Worker requires a production composition root with Postgres, Redis, "
        "artifact storage, telemetry, sandbox, git, and agent client."
    )


async def execute_task_for_worker(task_id: str, root: CompositionRoot | Any | None = None) -> dict:
    composition = root or get_composition_root()
    async with composition.orchestrator() as orchestrator:
        result = await orchestrator.execute_queued_task(parse_task_id(task_id))
        if result is None:
            return {"skipped": True, "task_id": task_id}
        return result.model_dump(mode="json")


def register_worker_tasks() -> None:
    from ai_orchestrator.infrastructure.queue.celery_app import celery_app

    @celery_app.task(name="ai_orchestrator.execute_task")
    def execute_task(task_id: str) -> dict:
        import asyncio

        return asyncio.run(execute_task_for_worker(task_id))


try:
    from ai_orchestrator.infrastructure.queue.celery_app import celery_app as celery_app

    register_worker_tasks()
except ImportError:
    celery_app = None
