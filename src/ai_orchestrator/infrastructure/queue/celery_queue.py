from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from ai_orchestrator.interfaces.task_queue import TaskQueue


class CeleryTaskQueue(TaskQueue):
    def __init__(self, send_task: Callable[[str, list[str]], object] | None = None) -> None:
        self._send_task = send_task

    async def enqueue_task(self, task_id: UUID) -> None:
        self._sender()("ai_orchestrator.execute_task", [str(task_id)])

    def _sender(self) -> Callable[[str, list[str]], object]:
        if self._send_task is not None:
            return self._send_task
        from ai_orchestrator.infrastructure.queue.celery_app import celery_app

        return lambda name, args: celery_app.send_task(name, args=args)
