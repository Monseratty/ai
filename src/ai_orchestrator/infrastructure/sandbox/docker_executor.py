from __future__ import annotations

import asyncio

from ai_orchestrator.application.orchestrator.policies import ExecutionPolicy
from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxExecutor, SandboxPolicy, SandboxResult


class DockerSandboxExecutor(SandboxExecutor):
    def __init__(self, policy_validator: ExecutionPolicy | None = None) -> None:
        self._policy_validator = policy_validator or ExecutionPolicy()

    async def run(self, command: SandboxCommand, policy: SandboxPolicy) -> SandboxResult:
        self._policy_validator.validate_command(command, policy)
        docker_command = self.build_docker_command(command, policy)

        try:
            process = await asyncio.create_subprocess_exec(
                *docker_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=policy.timeout_seconds
            )
            return SandboxResult(
                exit_code=process.returncode or 0,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
            )
        except TimeoutError:
            return SandboxResult(exit_code=124, stdout="", stderr="Timed out", timed_out=True)

    def build_docker_command(self, command: SandboxCommand, policy: SandboxPolicy) -> list[str]:
        self._policy_validator.validate_command(command, policy)
        docker_command = [
            "docker",
            "run",
            "--rm",
            "--memory",
            policy.memory,
            "--cpus",
            str(policy.cpus),
            "--workdir",
            command.cwd,
        ]
        if policy.network_disabled:
            docker_command.extend(["--network", "none"])
        if policy.readonly_rootfs:
            docker_command.append("--read-only")
        if policy.workspace_host_path is not None:
            docker_command.extend(
                [
                    "--mount",
                    (
                        "type=bind,"
                        f"source={policy.workspace_host_path},"
                        f"target={policy.workspace_container_path}"
                    ),
                ]
            )
        docker_command.extend([policy.image, *command.command])
        return docker_command
