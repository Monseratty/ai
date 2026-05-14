from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_workflow_snapshot_exposes_workflow_and_tasks_for_api() -> None:
    asyncio.run(_assert_snapshot_exposes_workflow_and_tasks())


async def _assert_snapshot_exposes_workflow_and_tasks() -> None:
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=InMemoryTaskRepository(),
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.planner_with_two_tasks(),
        telemetry=InMemoryTelemetry(),
    )
    workflow = await service.create_workflow("Build API inspection")

    snapshot = await service.get_workflow_snapshot(workflow.id)

    assert snapshot.workflow.id == workflow.id
    assert len(snapshot.tasks) == 2
    assert snapshot.tasks[0].title == "Code: Build API inspection"
    assert snapshot.tasks[0].description == "Work on the user request: Build API inspection"
