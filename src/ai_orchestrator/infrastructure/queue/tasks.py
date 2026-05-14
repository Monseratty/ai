from __future__ import annotations

import asyncio
from collections.abc import Callable
from uuid import UUID

from ai_orchestrator.application.orchestrator.service import OrchestratorService


def parse_task_id(task_id: str) -> UUID:
    try:
        return UUID(task_id)
    except ValueError as exc:
        raise ValueError(f"Invalid task id: {task_id}") from exc


def execute_task_sync(
    task_id: str,
    orchestrator_factory: Callable[[], OrchestratorService],
) -> dict:
    result = asyncio.run(orchestrator_factory().execute_task(parse_task_id(task_id)))
    return result.model_dump(mode="json")


def register_celery_tasks(orchestrator_factory: Callable[[], OrchestratorService]) -> None:
    from ai_orchestrator.infrastructure.queue.celery_app import celery_app

    @celery_app.task(name="ai_orchestrator.execute_task")
    def execute_task(task_id: str) -> dict:
        return execute_task_sync(task_id, orchestrator_factory)
