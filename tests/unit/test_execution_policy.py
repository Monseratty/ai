from __future__ import annotations

import pytest
from pathlib import Path

from ai_orchestrator.application.orchestrator.policies import ExecutionPolicy, ToolPermissionError
from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxPolicy


def test_execution_policy_allows_explicitly_permitted_command() -> None:
    policy = SandboxPolicy(
        image="python:3.12-slim",
        allowed_commands={"pytest"},
        workspace_host_path=Path("/tmp/workspace"),
    )

    ExecutionPolicy().validate_command(SandboxCommand(command=["pytest", "-q"]), policy)


def test_execution_policy_rejects_command_outside_allowlist() -> None:
    policy = SandboxPolicy(image="python:3.12-slim", allowed_commands={"pytest"})

    with pytest.raises(ToolPermissionError):
        ExecutionPolicy().validate_command(SandboxCommand(command=["curl", "https://example.com"]), policy)


def test_execution_policy_requires_workspace_mount_by_default() -> None:
    policy = SandboxPolicy(image="python:3.12-slim", allowed_commands={"pytest"})

    with pytest.raises(ToolPermissionError):
        ExecutionPolicy().validate_command(SandboxCommand(command=["pytest", "-q"]), policy)
