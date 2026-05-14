from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel


class SandboxWorkspace(BaseModel):
    path: Path


class SandboxWorkspaceManager:
    def __init__(self, *, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def prepare_workspace(self, *, repo_path: Path, workflow_id: str, task_id: str) -> SandboxWorkspace:
        source = repo_path.resolve()
        destination = (self._workspace_root / workflow_id / task_id).resolve()
        if not source.exists() or not source.is_dir():
            raise ValueError(f"Repository path does not exist or is not a directory: {repo_path}")
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                "__pycache__",
                ".pytest_cache",
                ".ruff_cache",
                ".mypy_cache",
                ".venv",
                "node_modules",
                ".artifacts",
            ),
        )
        return SandboxWorkspace(path=destination)

    def cleanup_workspace(self, workspace: SandboxWorkspace) -> None:
        workspace_path = workspace.path.resolve()
        root = self._workspace_root.resolve()
        if not workspace_path.is_relative_to(root):
            raise ValueError("Refusing to cleanup workspace outside sandbox root.")
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
