from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryExecutionEventRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_orchestrator_exposes_workflows_artifacts_and_execution_history() -> None:
    asyncio.run(_assert_observability_reads())


async def _assert_observability_reads() -> None:
    workflows = InMemoryWorkflowRepository()
    tasks = InMemoryTaskRepository()
    artifacts = InMemoryArtifactRepository()
    history = InMemoryExecutionEventRepository()
    service = OrchestratorService(
        workflows=workflows,
        tasks=tasks,
        artifacts=artifacts,
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        execution_events=history,
    )

    workflow = await service.create_workflow("Expose observability")
    coding_task = (await tasks.list_by_workflow(workflow.id))[0]
    await service.execute_task(coding_task.id)

    assert [item.id for item in await service.list_workflows()] == [workflow.id]
    assert len(await service.list_workflow_artifacts(workflow.id)) == 2
    assert [event.event_type for event in await service.list_execution_history(workflow.id)] == [
        "workflow.created",
        "workflow.planned",
        "task.approved",
    ]
