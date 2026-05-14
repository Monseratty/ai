from __future__ import annotations

from pathlib import Path

from ai_orchestrator.config.settings import Settings
from ai_orchestrator.infrastructure.composition import CompositionRoot
from ai_orchestrator.infrastructure.queue.celery_queue import CeleryTaskQueue
from ai_orchestrator.infrastructure.queue.memory import InMemoryTaskQueue
from ai_orchestrator.infrastructure.openai.agents_sdk_client import OpenAIAgentsSDKClient
from ai_orchestrator.infrastructure.testing.fakes import FakeAgentClient
from ai_orchestrator.infrastructure.git.composite import CompositeGitService
from ai_orchestrator.infrastructure.telemetry.logging import StructuredLoggingTelemetry
from ai_orchestrator.application.tools.permissions import ToolPermissionPolicy
from ai_orchestrator.infrastructure.composition import TestingUnitOfWork


def test_composition_root_builds_production_adapters_from_settings(tmp_path: Path) -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/test",
        artifact_root=tmp_path,
        openai_model="gpt-5.2",
        git_enabled=True,
        queue_backend="celery",
    )

    root = CompositionRoot(settings=settings)

    assert root.settings is settings
    assert root._session_factory is None
    assert isinstance(root.queue, CeleryTaskQueue)
    assert root.git is not None
    assert isinstance(root.telemetry, StructuredLoggingTelemetry)
    assert root.workspace_manager is not None
    assert root.sandbox is not None
    assert root.sandbox_validation is not None
    assert root.tool_executor is not None
    assert isinstance(root.tool_permission_policy, ToolPermissionPolicy)


def test_composition_root_uses_fake_agents_by_default_for_local_execution(tmp_path: Path) -> None:
    root = CompositionRoot(settings=Settings(artifact_root=tmp_path))

    assert isinstance(root.agent_client, FakeAgentClient)


def test_composition_root_can_use_openai_agents_backend(tmp_path: Path) -> None:
    root = CompositionRoot(settings=Settings(artifact_root=tmp_path, agent_backend="openai"))

    assert isinstance(root.agent_client, OpenAIAgentsSDKClient)


def test_composition_root_can_use_github_pull_request_provider(tmp_path: Path) -> None:
    root = CompositionRoot(
        settings=Settings(
            artifact_root=tmp_path,
            git_enabled=True,
            pull_request_provider="github",
            github_repository="acme/repo",
            github_token="token",
        )
    )

    assert isinstance(root.git, CompositeGitService)


def test_composition_root_disables_git_by_default_for_local_ui_mode(tmp_path: Path) -> None:
    root = CompositionRoot(settings=Settings(artifact_root=tmp_path))

    assert root.git is None


def test_composition_root_creates_orchestrator_for_unit_of_work(tmp_path: Path) -> None:
    settings = Settings(artifact_root=tmp_path)
    root = CompositionRoot(settings=settings)
    unit = root.testing_unit_of_work()

    orchestrator = root.orchestrator_for_unit_of_work(unit)

    assert orchestrator is not None
    assert unit.workflows is not None


def test_composition_root_can_use_shared_memory_state_backend(tmp_path: Path) -> None:
    root = CompositionRoot(settings=Settings(artifact_root=tmp_path, state_backend="memory"))

    async def read_units() -> None:
        async with root.unit() as first:
            async with root.unit() as second:
                assert isinstance(first, TestingUnitOfWork)
                assert first is second

    import asyncio

    asyncio.run(read_units())


def test_composition_root_uses_in_memory_queue_by_default_for_local_ui_mode(tmp_path: Path) -> None:
    root = CompositionRoot(settings=Settings(artifact_root=tmp_path))

    assert isinstance(root.queue, InMemoryTaskQueue)
