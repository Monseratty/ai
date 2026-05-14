from __future__ import annotations

from ai_orchestrator.interfaces.sandbox import SandboxCommand, SandboxPolicy


class ToolPermissionError(PermissionError):
    """Raised when a requested sandbox command violates execution policy."""


class ExecutionPolicy:
    def validate_command(self, command: SandboxCommand, policy: SandboxPolicy) -> None:
        if not command.command:
            raise ToolPermissionError("Sandbox command cannot be empty.")
        executable = command.command[0]
        if policy.allowed_commands and executable not in policy.allowed_commands:
            raise ToolPermissionError(f"Command {executable!r} is not allowed by policy.")
        if policy.require_workspace_mount and policy.workspace_host_path is None:
            raise ToolPermissionError("Sandbox execution requires an explicit workspace mount.")
