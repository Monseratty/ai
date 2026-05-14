from __future__ import annotations

from enum import Enum
from typing import Protocol

from pydantic import BaseModel


class CommitResult(BaseModel):
    sha: str
    message: str


class PullRequestResult(BaseModel):
    url: str
    number: int | None = None
    is_draft: bool = True


class PullRequestState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequestStatus(BaseModel):
    number: int
    url: str
    state: PullRequestState
    is_draft: bool
    is_merged: bool
    head_ref: str
    base_ref: str
    head_sha: str | None = None


class GitService(Protocol):
    async def create_branch(self, branch_name: str, base_ref: str = "main") -> None: ...

    async def diff(self) -> str: ...

    async def commit(self, message: str, paths: list[str]) -> CommitResult: ...

    async def push(self, branch_name: str, remote: str = "origin") -> None: ...

    async def rollback(self) -> None: ...

    async def open_pull_request(
        self, title: str, body: str, branch_name: str, base_ref: str = "main"
    ) -> PullRequestResult: ...

    async def get_pull_request_status(self, number: int) -> PullRequestStatus: ...
