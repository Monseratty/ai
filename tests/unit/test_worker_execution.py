from __future__ import annotations

import asyncio
from uuid import uuid4

from ai_orchestrator.domain.models.review import TaskExecutionResult
from ai_orchestrator.infrastructure.queue.worker import execute_task_for_worker


def test_execute_task_for_worker_uses_composition_scope() -> None:
    task_id = uuid4()
    calls: list[str] = []

    class FakeService:
        async def execute_queued_task(self, value):
            calls.append(str(value))
            return TaskExecutionResult(
                task_id=value,
                workflow_id=uuid4(),
                summary="ok",
            )

    class FakeScope:
        async def __aenter__(self):
            return FakeService()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeRoot:
        def orchestrator(self):
            return FakeScope()

    result = asyncio.run(execute_task_for_worker(str(task_id), root=FakeRoot()))

    assert calls == [str(task_id)]
    assert result["task_id"] == str(task_id)


def test_execute_task_for_worker_returns_skip_payload_when_task_not_claimed() -> None:
    task_id = uuid4()

    class FakeService:
        async def execute_queued_task(self, value):
            return None

    class FakeScope:
        async def __aenter__(self):
            return FakeService()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeRoot:
        def orchestrator(self):
            return FakeScope()

    result = asyncio.run(execute_task_for_worker(str(task_id), root=FakeRoot()))

    assert result == {"skipped": True, "task_id": str(task_id)}
