from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from ai_orchestrator.application.orchestrator.policies import ToolPermissionError
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspace
from ai_orchestrator.interfaces.sandbox import SandboxResult


class ToolRequest(BaseModel):
    tool_name: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)

    def as_command(self) -> list[str]:
        return [self.tool_name, *self.args]


class ToolExecutionResult(BaseModel):
    tool_name: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class SandboxRunner(Protocol):
    async def run(self, *, workspace: SandboxWorkspace, command: list[str]) -> SandboxResult: ...


class ToolExecutionService:
    def __init__(self, *, runner: SandboxRunner, allowed_tools: set[str]) -> None:
        self._runner = runner
        self._allowed_tools = allowed_tools

    async def execute(
        self,
        *,
        workspace: SandboxWorkspace,
        request: ToolRequest,
    ) -> ToolExecutionResult:
        if request.tool_name not in self._allowed_tools:
            raise ToolPermissionError(f"Tool {request.tool_name!r} is not allowed.")
        result = await self._runner.run(workspace=workspace, command=request.as_command())
        return ToolExecutionResult(
            tool_name=request.tool_name,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )
