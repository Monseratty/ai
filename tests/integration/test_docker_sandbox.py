from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest

from ai_orchestrator.infrastructure.sandbox.docker_executor import DockerSandboxExecutor
from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxPolicy


def require_integration() -> None:
    if os.getenv("AIO_RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Set AIO_RUN_INTEGRATION_TESTS=1 to run live integration tests.")


def test_docker_sandbox_runs_allowed_command_with_workspace(tmp_path: Path) -> None:
    require_integration()
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is not available.")
    asyncio.run(_assert_docker_sandbox_runs_allowed_command_with_workspace(tmp_path))


async def _assert_docker_sandbox_runs_allowed_command_with_workspace(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("hello")
    executor = DockerSandboxExecutor()
    result = await executor.run(
        SandboxCommand(command=["python", "-c", "print('ok')"]),
        SandboxPolicy(
            image="python:3.12-slim",
            allowed_commands={"python"},
            workspace_host_path=tmp_path,
        ),
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "ok"
