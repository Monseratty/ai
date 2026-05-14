from __future__ import annotations

from pathlib import Path

from ai_orchestrator.infrastructure.sandbox.docker_executor import DockerSandboxExecutor
from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxPolicy


def test_docker_executor_builds_restricted_container_command_with_workspace_mount() -> None:
    executor = DockerSandboxExecutor()
    policy = SandboxPolicy(
        image="python:3.12-slim",
        allowed_commands={"pytest"},
        workspace_host_path=Path("/tmp/workspace"),
        workspace_container_path="/workspace",
    )

    command = executor.build_docker_command(SandboxCommand(command=["pytest", "-q"]), policy)

    assert command == [
        "docker",
        "run",
        "--rm",
        "--memory",
        "1g",
        "--cpus",
        "1.0",
        "--workdir",
        "/workspace",
        "--network",
        "none",
        "--read-only",
        "--mount",
        "type=bind,source=/tmp/workspace,target=/workspace",
        "python:3.12-slim",
        "pytest",
        "-q",
    ]
