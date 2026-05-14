from __future__ import annotations

import asyncio
from pathlib import Path

from ai_orchestrator.infrastructure.sandbox.run_service import SandboxRunService
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace
from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxPolicy, SandboxResult


class RecordingSandboxExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[SandboxCommand, SandboxPolicy]] = []

    async def run(self, command: SandboxCommand, policy: SandboxPolicy) -> SandboxResult:
        self.calls.append((command, policy))
        return SandboxResult(exit_code=0, stdout="ok", stderr="")


def test_sandbox_run_service_mounts_workspace_and_restricts_commands(tmp_path: Path) -> None:
    asyncio.run(_assert_sandbox_run_service_mounts_workspace_and_restricts_commands(tmp_path))


async def _assert_sandbox_run_service_mounts_workspace_and_restricts_commands(tmp_path: Path) -> None:
    executor = RecordingSandboxExecutor()
    workspace = SandboxWorkspace(path=tmp_path / "workspace")
    service = SandboxRunService(
        executor=executor,
        base_policy=SandboxPolicy(image="python:3.12-slim", allowed_commands={"pytest"}),
    )

    result = await service.run(workspace=workspace, command=["pytest", "-q"])

    assert result.stdout == "ok"
    recorded_command, recorded_policy = executor.calls[0]
    assert recorded_command.command == ["pytest", "-q"]
    assert recorded_policy.workspace_host_path == workspace.path
    assert recorded_policy.workspace_container_path == "/workspace"
