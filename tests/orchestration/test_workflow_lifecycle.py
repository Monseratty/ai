from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.domain.enums import ReviewDecision, TaskKind, TaskStatus, WorkflowStatus
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryExecutionEventRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_user_task_is_decomposed_into_persisted_task_graph_and_ready_tasks_are_queued() -> None:
    asyncio.run(_assert_user_task_is_decomposed_into_persisted_task_graph())


async def _assert_user_task_is_decomposed_into_persisted_task_graph() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    queue = InMemoryTaskQueue()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=queue,
        agents=FakeAgentClient.planner_with_two_tasks(),
        telemetry=InMemoryTelemetry(),
    )

    workflow = await service.create_workflow("Build a typed FastAPI health endpoint")

    persisted = await workflows.get(workflow.id)
    planned_tasks = await tasks.list_by_workflow(workflow.id)

    assert persisted.status is WorkflowStatus.PLANNED
    assert [task.kind for task in planned_tasks] == [TaskKind.CODING, TaskKind.TESTING]
    assert planned_tasks[0].status is TaskStatus.QUEUED
    assert planned_tasks[1].status is TaskStatus.BLOCKED
    assert queue.enqueued_task_ids == [planned_tasks[0].id]


def test_coding_task_requires_reviewer_approval_before_workflow_can_complete() -> None:
    asyncio.run(_assert_coding_task_requires_reviewer_approval())


async def _assert_coding_task_requires_reviewer_approval() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    artifacts = InMemoryArtifactRepository()
    queue = InMemoryTaskQueue()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=artifacts,
        queue=queue,
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
    )

    workflow = await service.create_workflow("Add repository interfaces")
    coding_task = (await tasks.list_by_workflow(workflow.id))[0]

    result = await service.execute_task(coding_task.id)

    assert result.review_decision is ReviewDecision.APPROVE
    assert (await tasks.get(coding_task.id)).status is TaskStatus.SUCCEEDED
    assert len(await artifacts.list_by_task(coding_task.id)) == 2
    assert (await workflows.get(workflow.id)).status is WorkflowStatus.IN_PROGRESS


def test_reviewer_rejection_creates_bounded_feedback_task_without_infinite_loop() -> None:
    asyncio.run(_assert_reviewer_rejection_creates_bounded_feedback_task())


async def _assert_reviewer_rejection_creates_bounded_feedback_task() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    queue = InMemoryTaskQueue()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=queue,
        agents=FakeAgentClient.rejecting_code_review(),
        telemetry=InMemoryTelemetry(),
        max_feedback_attempts=1,
    )

    workflow = await service.create_workflow("Implement sandbox policies")
    coding_task = (await tasks.list_by_workflow(workflow.id))[0]

    result = await service.execute_task(coding_task.id)

    workflow_tasks = await tasks.list_by_workflow(workflow.id)
    feedback_tasks = [task for task in workflow_tasks if task.kind is TaskKind.FEEDBACK_FIX]

    assert result.review_decision is ReviewDecision.REQUEST_FIXES
    assert (await tasks.get(coding_task.id)).status is TaskStatus.REQUIRES_FIXES
    assert len(feedback_tasks) == 1
    assert feedback_tasks[0].attempt_count == 0
    assert feedback_tasks[0].max_attempts == 1
    assert queue.enqueued_task_ids[-1] == feedback_tasks[0].id


def test_full_task_graph_lifecycle_queues_dependents_and_completes_workflow() -> None:
    asyncio.run(_assert_full_task_graph_lifecycle())


async def _assert_full_task_graph_lifecycle() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    queue = InMemoryTaskQueue()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=queue,
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
    )

    workflow = await service.create_workflow("Implement full lifecycle")
    planned_tasks = await tasks.list_by_workflow(workflow.id)
    coding_task = planned_tasks[0]
    testing_task = planned_tasks[1]

    await service.execute_task(coding_task.id)

    assert (await tasks.get(testing_task.id)).status is TaskStatus.QUEUED
    assert queue.enqueued_task_ids[-1] == testing_task.id

    await service.execute_task(testing_task.id)

    assert (await tasks.get(testing_task.id)).status is TaskStatus.SUCCEEDED
    assert (await workflows.get(workflow.id)).status is WorkflowStatus.SUCCEEDED


def test_orchestrator_persists_execution_history_events_when_repository_is_configured() -> None:
    asyncio.run(_assert_orchestrator_persists_execution_history_events())


async def _assert_orchestrator_persists_execution_history_events() -> None:
    execution_events = InMemoryExecutionEventRepository()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=InMemoryTaskRepository(),
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        execution_events=execution_events,
    )

    workflow = await service.create_workflow("Record execution history")
    coding_task = (await service.get_workflow_snapshot(workflow.id)).tasks[0]

    await service.execute_task(coding_task.id)

    event_types = [event.event_type for event in await execution_events.list_by_workflow(workflow.id)]
    assert event_types == ["workflow.created", "workflow.planned", "task.approved"]
