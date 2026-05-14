from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class CommitResult(BaseModel):
    sha: str
    message: str


class PullRequestResult(BaseModel):
    url: str
    number: int | None = None
    is_draft: bool = True


class GitService(Protocol):
    async def create_branch(self, branch_name: str, base_ref: str = "main") -> None: ...

    async def diff(self) -> str: ...

    async def commit(self, message: str, paths: list[str]) -> CommitResult: ...

    async def rollback(self) -> None: ...

    async def open_pull_request(
        self, title: str, body: str, branch_name: str, base_ref: str = "main"
    ) -> PullRequestResult: ...

