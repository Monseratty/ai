from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ai_orchestrator.application.tools.execution import ToolExecutionService, ToolRequest
from ai_orchestrator.application.tools.permissions import ToolPermissionPolicy
from ai_orchestrator.application.orchestrator.policies import ToolPermissionError
from ai_orchestrator.domain.enums import AgentType, TaskKind
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace
from ai_orchestrator.interfaces.sandbox import SandboxResult


class RecordingRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    async def run(self, *, workspace: SandboxWorkspace, command: list[str]) -> SandboxResult:
        self.commands.append(command)
        return SandboxResult(exit_code=0, stdout="ok", stderr="")


def test_tool_execution_service_runs_allowed_sandbox_command() -> None:
    asyncio.run(_assert_tool_execution_service_runs_allowed_sandbox_command())


async def _assert_tool_execution_service_runs_allowed_sandbox_command() -> None:
    runner = RecordingRunner()
    service = ToolExecutionService(runner=runner, allowed_tools={"pytest"})
    workspace = SandboxWorkspace(path=Path("/tmp/workspace"))

    result = await service.execute(
        workspace=workspace,
        request=ToolRequest(tool_name="pytest", args=["-q"]),
    )

    assert result.ok is True
    assert result.exit_code == 0
    assert result.stdout == "ok"
    assert runner.commands == [["pytest", "-q"]]


def test_tool_execution_service_rejects_disallowed_tool() -> None:
    async def run() -> None:
        service = ToolExecutionService(runner=RecordingRunner(), allowed_tools={"pytest"})
        await service.execute(
            workspace=SandboxWorkspace(path=Path("/tmp/workspace")),
            request=ToolRequest(tool_name="curl", args=["https://example.com"]),
        )

    with pytest.raises(ToolPermissionError):
        asyncio.run(run())


def test_tool_execution_service_applies_agent_and_task_scoped_permissions() -> None:
    asyncio.run(_assert_tool_execution_service_applies_agent_and_task_scoped_permissions())


async def _assert_tool_execution_service_applies_agent_and_task_scoped_permissions() -> None:
    runner = RecordingRunner()
    policy = ToolPermissionPolicy(
        grants={
            (AgentType.TESTER, TaskKind.TESTING): {"pytest"},
            (AgentType.CODER, TaskKind.CODING): {"python"},
        }
    )
    service = ToolExecutionService(
        runner=runner,
        allowed_tools={"python", "pytest"},
        permission_policy=policy,
    )
    workspace = SandboxWorkspace(path=Path("/tmp/workspace"))

    await service.execute(
        workspace=workspace,
        request=ToolRequest(tool_name="pytest", args=["-q"]),
        agent_type=AgentType.TESTER,
        task_kind=TaskKind.TESTING,
    )

    with pytest.raises(ToolPermissionError):
        await service.execute(
            workspace=workspace,
            request=ToolRequest(tool_name="pytest", args=["-q"]),
            agent_type=AgentType.CODER,
            task_kind=TaskKind.CODING,
        )

    assert runner.commands == [["pytest", "-q"]]
