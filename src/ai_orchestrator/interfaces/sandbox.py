from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class SandboxPolicy(BaseModel):
    image: str
    timeout_seconds: int = Field(default=300, ge=1)
    memory: str = "1g"
    cpus: float = Field(default=1.0, gt=0)
    network_disabled: bool = True
    readonly_rootfs: bool = True
    allowed_commands: set[str] = Field(default_factory=set)
    workspace_host_path: Path | None = None
    workspace_container_path: str = "/workspace"
    require_workspace_mount: bool = True


class SandboxCommand(BaseModel):
    command: list[str]
    cwd: str = "/workspace"


class SandboxResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SandboxExecutor(Protocol):
    async def run(self, command: SandboxCommand, policy: SandboxPolicy) -> SandboxResult: ...
