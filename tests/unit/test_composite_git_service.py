from __future__ import annotations

import asyncio

from ai_orchestrator.infrastructure.git.composite import CompositeGitService
from ai_orchestrator.infrastructure.testing.fakes import FakeGitService
from ai_orchestrator.interfaces.git import PullRequestResult


class FakePullRequestProvider:
    def __init__(self) -> None:
        self.calls = []

    async def open_pull_request(self, *, title: str, body: str, branch_name: str, base_ref: str):
        self.calls.append((title, body, branch_name, base_ref))
        return PullRequestResult(url="https://example.test/pr/1", number=1, is_draft=True)


def test_composite_git_service_delegates_prs_to_provider_and_commits_to_local_git() -> None:
    asyncio.run(_assert_composite_git_service_delegates_prs_to_provider_and_commits_to_local_git())


async def _assert_composite_git_service_delegates_prs_to_provider_and_commits_to_local_git() -> None:
    local = FakeGitService()
    provider = FakePullRequestProvider()
    service = CompositeGitService(local=local, pull_requests=provider)

    await service.commit("message", ["file.py"])
    result = await service.open_pull_request(
        title="PR",
        body="Body",
        branch_name="codex/work",
        base_ref="main",
    )

    assert local.commits == [("message", ["file.py"])]
    assert result.url == "https://example.test/pr/1"
    assert provider.calls == [("PR", "Body", "codex/work", "main")]
