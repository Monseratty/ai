from __future__ import annotations

from pathlib import Path

from ai_orchestrator.interfaces.git import (
    CommitResult,
    GitService,
    PullRequestResult,
    PullRequestState,
    PullRequestStatus,
)


class GitPythonService(GitService):
    def __init__(self, repo_path: Path) -> None:
        self._repo_path = repo_path

    async def create_branch(self, branch_name: str, base_ref: str = "main") -> None:
        from git import Repo

        repo = Repo(self._repo_path)
        repo.git.checkout(base_ref)
        repo.git.checkout("-B", branch_name)

    async def diff(self) -> str:
        from git import Repo

        repo = Repo(self._repo_path)
        return repo.git.diff()

    async def commit(self, message: str, paths: list[str]) -> CommitResult:
        from git import Repo

        repo = Repo(self._repo_path)
        repo.index.add(paths)
        commit = repo.index.commit(message)
        return CommitResult(sha=commit.hexsha, message=message)

    async def push(self, branch_name: str, remote: str = "origin") -> None:
        from git import Repo

        repo = Repo(self._repo_path)
        repo.git.push("-u", remote, branch_name)

    async def rollback(self) -> None:
        from git import Repo

        repo = Repo(self._repo_path)
        repo.git.reset("--hard", "HEAD")

    async def open_pull_request(
        self, title: str, body: str, branch_name: str, base_ref: str = "main"
    ) -> PullRequestResult:
        return PullRequestResult(
            url=f"local://pull-request/{branch_name}?base={base_ref}",
            number=None,
            is_draft=True,
        )

    async def get_pull_request_status(self, number: int) -> PullRequestStatus:
        return PullRequestStatus(
            number=number,
            url=f"local://pull-request/{number}",
            state=PullRequestState.OPEN,
            is_draft=True,
            is_merged=False,
            head_ref="local",
            base_ref="main",
        )
