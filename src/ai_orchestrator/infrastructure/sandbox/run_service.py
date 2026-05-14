from __future__ import annotations

from copy import deepcopy

from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace
from ai_orchestrator.interfaces.sandbox import (
    SandboxCommand,
    SandboxExecutor,
    SandboxPolicy,
    SandboxResult,
)


class SandboxRunService:
    def __init__(self, *, executor: SandboxExecutor, base_policy: SandboxPolicy) -> None:
        self._executor = executor
        self._base_policy = base_policy

    async def run(self, *, workspace: SandboxWorkspace, command: list[str]) -> SandboxResult:
        policy = deepcopy(self._base_policy)
        policy.workspace_host_path = workspace.path
        policy.workspace_container_path = "/workspace"
        return await self._executor.run(
            SandboxCommand(command=command, cwd=policy.workspace_container_path),
            policy,
        )
