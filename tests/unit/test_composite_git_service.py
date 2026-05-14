from __future__ import annotations

import asyncio

from ai_orchestrator.infrastructure.git.composite import CompositeGitService
from ai_orchestrator.infrastructure.testing.fakes import FakeGitService
from ai_orchestrator.interfaces.git import (
    CheckRunConclusion,
    CheckRunResult,
    CheckRunStatus,
    PullRequestResult,
    PullRequestState,
    PullRequestStatus,
)


class FakePullRequestProvider:
    def __init__(self) -> None:
        self.calls = []

    async def open_pull_request(self, *, title: str, body: str, branch_name: str, base_ref: str):
        self.calls.append((title, body, branch_name, base_ref))
        return PullRequestResult(url="https://example.test/pr/1", number=1, is_draft=True)

    async def get_pull_request_status(self, number: int) -> PullRequestStatus:
        return PullRequestStatus(
            number=number,
            url=f"https://example.test/pr/{number}",
            state=PullRequestState.OPEN,
            is_draft=False,
            is_merged=False,
            head_ref="codex/work",
            base_ref="main",
        )

    async def report_check_run(
        self,
        *,
        name: str,
        head_sha: str,
        status: CheckRunStatus,
        conclusion: CheckRunConclusion | None = None,
        summary: str,
        details_url: str | None = None,
    ) -> CheckRunResult:
        self.calls.append((name, head_sha, status, conclusion, summary, details_url))
        return CheckRunResult(provider_id="99", url="https://example.test/runs/99")


def test_composite_git_service_delegates_prs_to_provider_and_commits_to_local_git() -> None:
    asyncio.run(_assert_composite_git_service_delegates_prs_to_provider_and_commits_to_local_git())


async def _assert_composite_git_service_delegates_prs_to_provider_and_commits_to_local_git() -> None:
    local = FakeGitService()
    provider = FakePullRequestProvider()
    service = CompositeGitService(local=local, pull_requests=provider)

    await service.commit("message", ["file.py"])
    await service.push("codex/work", remote="origin")
    result = await service.open_pull_request(
        title="PR",
        body="Body",
        branch_name="codex/work",
        base_ref="main",
    )
    status = await service.get_pull_request_status(1)
    check = await service.report_check_run(
        name="AI Orchestrator",
        head_sha="abc123",
        status=CheckRunStatus.COMPLETED,
        conclusion=CheckRunConclusion.SUCCESS,
        summary="Passed",
    )

    assert local.commits == [("message", ["file.py"])]
    assert local.pushes == [("codex/work", "origin")]
    assert result.url == "https://example.test/pr/1"
    assert status.state is PullRequestState.OPEN
    assert check.provider_id == "99"
    assert provider.calls == [
        ("PR", "Body", "codex/work", "main"),
        (
            "AI Orchestrator",
            "abc123",
            CheckRunStatus.COMPLETED,
            CheckRunConclusion.SUCCESS,
            "Passed",
            None,
        ),
    ]
