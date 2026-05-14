from __future__ import annotations

from typing import Protocol

from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace
from ai_orchestrator.interfaces.sandbox import SandboxResult


class SandboxRunner(Protocol):
    async def run(self, *, workspace: SandboxWorkspace, command: list[str]) -> SandboxResult: ...


class SandboxValidationService:
    def __init__(self, *, runner: SandboxRunner) -> None:
        self._runner = runner

    async def run_pytest(self, workspace: SandboxWorkspace) -> SandboxResult:
        return await self._runner.run(workspace=workspace, command=["pytest", "-q"])
