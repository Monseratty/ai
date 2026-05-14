from __future__ import annotations

from uuid import UUID

from ai_orchestrator.interfaces.task_queue import TaskQueue


class InMemoryTaskQueue(TaskQueue):
    def __init__(self) -> None:
        self.enqueued_task_ids: list[UUID] = []

    async def enqueue_task(self, task_id: UUID) -> None:
        self.enqueued_task_ids.append(task_id)
