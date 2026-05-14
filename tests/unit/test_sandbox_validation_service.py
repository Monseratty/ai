from __future__ import annotations

import asyncio
from pathlib import Path

from ai_orchestrator.application.sandbox.validation import SandboxValidationService
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace
from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxPolicy, SandboxResult


class RecordingSandboxRunService:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    async def run(self, *, workspace: SandboxWorkspace, command: list[str]) -> SandboxResult:
        self.commands.append(command)
        return SandboxResult(exit_code=0, stdout="passed", stderr="")


def test_sandbox_validation_service_runs_pytest_in_workspace() -> None:
    asyncio.run(_assert_sandbox_validation_service_runs_pytest_in_workspace())


async def _assert_sandbox_validation_service_runs_pytest_in_workspace() -> None:
    runner = RecordingSandboxRunService()
    service = SandboxValidationService(runner=runner)
    workspace = SandboxWorkspace(path=Path("/tmp/workspace"))

    result = await service.run_pytest(workspace)

    assert result.exit_code == 0
    assert runner.commands == [["pytest", "-q"]]
