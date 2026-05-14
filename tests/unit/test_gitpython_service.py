from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("git")

from git import Repo  # noqa: E402

from ai_orchestrator.infrastructure.git.gitpython_repo import GitPythonService  # noqa: E402


def test_gitpython_service_creates_branch_diff_commit_and_rollback(tmp_path) -> None:
    asyncio.run(_assert_gitpython_service_creates_branch_diff_commit_and_rollback(tmp_path))


async def _assert_gitpython_service_creates_branch_diff_commit_and_rollback(tmp_path) -> None:
    repo = Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    (tmp_path / "README.md").write_text("initial\n")
    repo.index.add(["README.md"])
    repo.index.commit("initial")

    service = GitPythonService(tmp_path)
    await service.create_branch("codex/work", base_ref=repo.active_branch.name)
    (tmp_path / "README.md").write_text("changed\n")

    diff = await service.diff()
    commit = await service.commit("change readme", ["README.md"])

    assert "-initial" in diff
    assert "+changed" in diff
    assert len(commit.sha) == 40

    (tmp_path / "README.md").write_text("broken\n")
    await service.rollback()

    assert (tmp_path / "README.md").read_text() == "changed\n"
