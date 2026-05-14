from __future__ import annotations

from typing import Protocol

from ai_orchestrator.interfaces.git import CommitResult, GitService, PullRequestResult


class PullRequestProvider(Protocol):
    async def open_pull_request(
        self,
        *,
        title: str,
        body: str,
        branch_name: str,
        base_ref: str = "main",
    ) -> PullRequestResult: ...


class CompositeGitService(GitService):
    def __init__(self, *, local: GitService, pull_requests: PullRequestProvider) -> None:
        self._local = local
        self._pull_requests = pull_requests

    async def create_branch(self, branch_name: str, base_ref: str = "main") -> None:
        await self._local.create_branch(branch_name, base_ref)

    async def diff(self) -> str:
        return await self._local.diff()

    async def commit(self, message: str, paths: list[str]) -> CommitResult:
        return await self._local.commit(message, paths)

    async def push(self, branch_name: str, remote: str = "origin") -> None:
        await self._local.push(branch_name, remote)

    async def rollback(self) -> None:
        await self._local.rollback()

    async def open_pull_request(
        self, title: str, body: str, branch_name: str, base_ref: str = "main"
    ) -> PullRequestResult:
        return await self._pull_requests.open_pull_request(
            title=title,
            body=body,
            branch_name=branch_name,
            base_ref=base_ref,
        )
