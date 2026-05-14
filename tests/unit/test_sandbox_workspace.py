from __future__ import annotations

from pathlib import Path

from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspaceManager


def test_workspace_manager_creates_isolated_copy_without_git_metadata(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".git" / "config").write_text("secret-ish metadata")
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('ok')\n")
    workspace_root = tmp_path / "sandboxes"
    manager = SandboxWorkspaceManager(workspace_root=workspace_root)

    workspace = manager.prepare_workspace(repo_path=repo, workflow_id="wf-1", task_id="task-1")

    assert workspace.path == workspace_root / "wf-1" / "task-1"
    assert (workspace.path / "pyproject.toml").exists()
    assert (workspace.path / "src" / "app.py").exists()
    assert not (workspace.path / ".git").exists()
    assert (repo / ".git" / "config").exists()


def test_workspace_manager_replaces_existing_task_workspace(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.txt").write_text("fresh")
    manager = SandboxWorkspaceManager(workspace_root=tmp_path / "sandboxes")

    workspace = manager.prepare_workspace(repo_path=repo, workflow_id="wf", task_id="task")
    (workspace.path / "stale.txt").write_text("stale")
    workspace = manager.prepare_workspace(repo_path=repo, workflow_id="wf", task_id="task")

    assert not (workspace.path / "stale.txt").exists()
    assert (workspace.path / "file.txt").read_text() == "fresh"
