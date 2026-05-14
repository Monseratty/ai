from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.infrastructure.artifacts.filesystem import FilesystemArtifactStore
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def test_orchestrator_materializes_inline_agent_artifacts(tmp_path) -> None:
    asyncio.run(_assert_orchestrator_materializes_inline_agent_artifacts(tmp_path))


async def _assert_orchestrator_materializes_inline_agent_artifacts(tmp_path) -> None:
    artifacts = InMemoryArtifactRepository()
    tasks = InMemoryTaskRepository()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=tasks,
        artifacts=artifacts,
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        artifact_store=FilesystemArtifactStore(tmp_path),
    )
    workflow = await service.create_workflow("Materialize artifacts")
    coding_task = (await tasks.list_by_workflow(workflow.id))[0]

    await service.execute_task(coding_task.id)

    stored = await artifacts.list_by_task(coding_task.id)
    assert len(stored) == 2
    assert all(artifact.path is not None for artifact in stored)
    assert all((tmp_path / artifact.path).exists() for artifact in stored if artifact.path is not None)
