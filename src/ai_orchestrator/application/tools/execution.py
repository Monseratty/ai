from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from ai_orchestrator.application.orchestrator.policies import ToolPermissionError
from ai_orchestrator.application.tools.permissions import ToolPermissionPolicy
from ai_orchestrator.domain.enums import AgentType, TaskKind
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
    def __init__(
        self,
        *,
        runner: SandboxRunner,
        allowed_tools: set[str],
        permission_policy: ToolPermissionPolicy | None = None,
    ) -> None:
        self._runner = runner
        self._allowed_tools = allowed_tools
        self._permission_policy = permission_policy

    async def execute(
        self,
        *,
        workspace: SandboxWorkspace,
        request: ToolRequest,
        agent_type: AgentType | None = None,
        task_kind: TaskKind | None = None,
    ) -> ToolExecutionResult:
        if request.tool_name not in self._allowed_tools:
            raise ToolPermissionError(f"Tool {request.tool_name!r} is not allowed.")
        if self._permission_policy is not None:
            self._permission_policy.validate(
                tool_name=request.tool_name,
                agent_type=agent_type,
                task_kind=task_kind,
            )
        result = await self._runner.run(workspace=workspace, command=request.as_command())
        return ToolExecutionResult(
            tool_name=request.tool_name,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )
