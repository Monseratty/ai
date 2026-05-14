from __future__ import annotations

import asyncio
from uuid import uuid4

from ai_orchestrator.infrastructure.queue.celery_queue import CeleryTaskQueue


def test_celery_task_queue_sends_execute_task_message() -> None:
    asyncio.run(_assert_celery_task_queue_sends_execute_task_message())


async def _assert_celery_task_queue_sends_execute_task_message() -> None:
    sent: list[tuple[str, list[str]]] = []

    def send_task(name: str, args: list[str]) -> None:
        sent.append((name, args))

    task_id = uuid4()
    queue = CeleryTaskQueue(send_task=send_task)

    await queue.enqueue_task(task_id)

    assert sent == [("ai_orchestrator.execute_task", [str(task_id)])]
