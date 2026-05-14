from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.domain.enums import TaskStatus
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_execute_queued_task_skips_already_completed_task() -> None:
    asyncio.run(_assert_execute_queued_task_skips_already_completed_task())


async def _assert_execute_queued_task_skips_already_completed_task() -> None:
    tasks = InMemoryTaskRepository()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
    )
    workflow = await service.create_workflow("Skip completed task")
    task = (await tasks.list_by_workflow(workflow.id))[0]
    await tasks.update(task.with_status(TaskStatus.SUCCEEDED))

    result = await service.execute_queued_task(task.id)

    assert result is None
    assert (await tasks.get(task.id)).status is TaskStatus.SUCCEEDED
