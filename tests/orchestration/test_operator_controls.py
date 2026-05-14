from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.domain.enums import TaskStatus, WorkflowStatus
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryExecutionEventRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_retry_task_resets_failed_task_to_queued_and_enqueues_it() -> None:
    asyncio.run(_assert_retry_task_resets_failed_task_to_queued_and_enqueues_it())


async def _assert_retry_task_resets_failed_task_to_queued_and_enqueues_it() -> None:
    tasks = InMemoryTaskRepository()
    queue = InMemoryTaskQueue()
    history = InMemoryExecutionEventRepository()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=queue,
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        execution_events=history,
    )
    workflow = await service.create_workflow("Retry task")
    task = (await tasks.list_by_workflow(workflow.id))[0]
    await tasks.update(task.with_status(TaskStatus.FAILED))

    retried = await service.retry_task(task.id)

    assert retried.status is TaskStatus.QUEUED
    assert queue.enqueued_task_ids[-1] == task.id
    event_types = [event.event_type for event in await history.list_by_workflow(workflow.id)]
    assert "task.retry_queued" in event_types


def test_cancel_workflow_cancels_non_terminal_tasks_and_workflow() -> None:
    asyncio.run(_assert_cancel_workflow_cancels_non_terminal_tasks_and_workflow())


async def _assert_cancel_workflow_cancels_non_terminal_tasks_and_workflow() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
    )
    workflow = await service.create_workflow("Cancel workflow")

    cancelled = await service.cancel_workflow(workflow.id)

    assert cancelled.status is WorkflowStatus.CANCELLED
    assert {task.status for task in await tasks.list_by_workflow(workflow.id)} == {TaskStatus.CANCELLED}
