from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.infrastructure.telemetry.memory import InMemoryTelemetry
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryWorkflowRepository,
)


def test_orchestrator_emits_metrics_for_workflow_and_task_execution() -> None:
    asyncio.run(_assert_orchestrator_emits_metrics_for_workflow_and_task_execution())


async def _assert_orchestrator_emits_metrics_for_workflow_and_task_execution() -> None:
    telemetry = InMemoryTelemetry()
    tasks = InMemoryTaskRepository()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=telemetry,
    )

    workflow = await service.create_workflow("Emit metrics")
    task = (await tasks.list_by_workflow(workflow.id))[0]
    await service.execute_task(task.id)

    counter_names = [name for name, _, _ in telemetry.counters]
    observation_names = [name for name, _, _ in telemetry.observations]

    assert "workflows.created" in counter_names
    assert "tasks.approved" in counter_names
    assert "tasks.execution_duration_ms" in observation_names
