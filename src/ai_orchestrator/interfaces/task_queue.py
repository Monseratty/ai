from __future__ import annotations

from typing import Protocol
from uuid import UUID


class TaskQueue(Protocol):
    async def enqueue_task(self, task_id: UUID) -> None: ...

