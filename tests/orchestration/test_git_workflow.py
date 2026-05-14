from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.domain.enums import WorkflowStatus
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    FakeGitService,
    InMemoryArtifactRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_orchestrator_commits_after_workflow_success_without_opening_pr() -> None:
    asyncio.run(_assert_orchestrator_commits_after_workflow_success_without_opening_pr())


async def _assert_orchestrator_commits_after_workflow_success_without_opening_pr() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    git = FakeGitService()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        git=git,
    )

    workflow = await service.create_workflow("Commit successful workflow")
    coding_task, testing_task = await tasks.list_by_workflow(workflow.id)

    await service.execute_task(coding_task.id)
    await service.execute_task(testing_task.id)

    completed = await workflows.get(workflow.id)
    assert completed.status is WorkflowStatus.SUCCEEDED
    assert git.commits == [("Complete workflow: Commit successful workflow", ["src/example.py"])]
    assert git.pull_requests == []


def test_orchestrator_rolls_back_and_fails_workflow_when_commit_fails() -> None:
    asyncio.run(_assert_orchestrator_rolls_back_and_fails_workflow_when_commit_fails())


async def _assert_orchestrator_rolls_back_and_fails_workflow_when_commit_fails() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    git = FakeGitService()
    git.fail_commit = True
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        git=git,
    )

    workflow = await service.create_workflow("Rollback failed commit")
    coding_task, testing_task = await tasks.list_by_workflow(workflow.id)

    await service.execute_task(coding_task.id)
    await service.execute_task(testing_task.id)

    assert (await workflows.get(workflow.id)).status is WorkflowStatus.FAILED
    assert git.rollback_count == 1
