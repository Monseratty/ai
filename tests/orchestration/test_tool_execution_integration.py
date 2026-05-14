from __future__ import annotations

import asyncio
from pathlib import Path

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.application.tools.execution import ToolExecutionService
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace, SandboxWorkspaceManager
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)
from ai_orchestrator.interfaces.sandbox import SandboxResult


class RecordingRunner:
    def __init__(self, *, exit_code: int = 0) -> None:
        self.commands: list[list[str]] = []
        self.exit_code = exit_code

    async def run(self, *, workspace: SandboxWorkspace, command: list[str]) -> SandboxResult:
        self.commands.append(command)
        return SandboxResult(exit_code=self.exit_code, stdout="tool ok", stderr="failed")


def test_orchestrator_executes_agent_tool_requests_in_sandbox_workspace(tmp_path: Path) -> None:
    asyncio.run(_assert_orchestrator_executes_agent_tool_requests_in_sandbox_workspace(tmp_path))


async def _assert_orchestrator_executes_agent_tool_requests_in_sandbox_workspace(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n")
    artifacts = InMemoryArtifactRepository()
    tasks = InMemoryTaskRepository()
    runner = RecordingRunner()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=tasks,
        artifacts=artifacts,
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review_with_tool_requests(),
        telemetry=InMemoryTelemetry(),
        workspace_manager=SandboxWorkspaceManager(workspace_root=tmp_path / "sandboxes"),
        repo_path=repo,
        tool_executor=ToolExecutionService(runner=runner, allowed_tools={"pytest"}),
    )

    workflow = await service.create_workflow("Run tool requests")
    coding_task = (await tasks.list_by_workflow(workflow.id))[0]

    await service.execute_task(coding_task.id)

    assert runner.commands == [["pytest", "-q"], ["pytest", "-q"]]
    stored = await artifacts.list_by_task(coding_task.id)
    assert any(artifact.kind == "tool_result" for artifact in stored)


def test_orchestrator_marks_task_failed_when_sandbox_tool_fails(tmp_path: Path) -> None:
    asyncio.run(_assert_orchestrator_marks_task_failed_when_sandbox_tool_fails(tmp_path))


async def _assert_orchestrator_marks_task_failed_when_sandbox_tool_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n")
    tasks = InMemoryTaskRepository()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=tasks,
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review_with_tool_requests(),
        telemetry=InMemoryTelemetry(),
        workspace_manager=SandboxWorkspaceManager(workspace_root=tmp_path / "sandboxes"),
        repo_path=repo,
        tool_executor=ToolExecutionService(runner=RecordingRunner(exit_code=1), allowed_tools={"pytest"}),
    )
    workflow = await service.create_workflow("Fail on tool error")
    coding_task = (await tasks.list_by_workflow(workflow.id))[0]

    await service.execute_task(coding_task.id)

    assert (await tasks.get(coding_task.id)).status.value == "failed"
