from __future__ import annotations

import asyncio

from ai_orchestrator.infrastructure.git.github_pr import GitHubPullRequestProvider
from ai_orchestrator.interfaces.git import CheckRunConclusion, CheckRunStatus, PullRequestState


def test_github_pull_request_provider_posts_expected_payload() -> None:
    asyncio.run(_assert_github_pull_request_provider_posts_expected_payload())


def test_github_pull_request_provider_reads_pr_status() -> None:
    asyncio.run(_assert_github_pull_request_provider_reads_pr_status())


def test_github_provider_creates_check_run() -> None:
    asyncio.run(_assert_github_provider_creates_check_run())


async def _assert_github_pull_request_provider_posts_expected_payload() -> None:
    calls = []

    async def sender(method: str, url: str, headers: dict, json: dict):
        calls.append((method, url, headers, json))
        return {"html_url": "https://github.com/acme/repo/pull/7", "number": 7, "draft": True}

    provider = GitHubPullRequestProvider(
        repository_full_name="acme/repo",
        token="token",
        sender=sender,
    )

    result = await provider.open_pull_request(
        title="Complete workflow",
        body="Summary",
        branch_name="codex/work",
        base_ref="main",
    )

    assert result.url == "https://github.com/acme/repo/pull/7"
    assert result.number == 7
    assert calls == [
        (
            "POST",
            "https://api.github.com/repos/acme/repo/pulls",
            {
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer token",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            {
                "title": "Complete workflow",
                "body": "Summary",
                "head": "codex/work",
                "base": "main",
                "draft": True,
            },
        )
    ]


async def _assert_github_pull_request_provider_reads_pr_status() -> None:
    calls = []

    async def sender(method: str, url: str, headers: dict, json: dict):
        calls.append((method, url, headers, json))
        return {
            "html_url": "https://github.com/acme/repo/pull/7",
            "number": 7,
            "state": "open",
            "draft": False,
            "merged": False,
            "head": {"ref": "codex/work", "sha": "abc123"},
            "base": {"ref": "main"},
        }

    provider = GitHubPullRequestProvider(
        repository_full_name="acme/repo",
        token="token",
        sender=sender,
    )

    status = await provider.get_pull_request_status(7)

    assert status.number == 7
    assert status.url == "https://github.com/acme/repo/pull/7"
    assert status.state is PullRequestState.OPEN
    assert status.is_draft is False
    assert status.is_merged is False
    assert status.head_ref == "codex/work"
    assert status.head_sha == "abc123"
    assert status.base_ref == "main"
    assert calls == [
        (
            "GET",
            "https://api.github.com/repos/acme/repo/pulls/7",
            {
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer token",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            {},
        )
    ]


async def _assert_github_provider_creates_check_run() -> None:
    calls = []

    async def sender(method: str, url: str, headers: dict, json: dict):
        calls.append((method, url, headers, json))
        return {
            "id": 99,
            "html_url": "https://github.com/acme/repo/runs/99",
            "status": "completed",
            "conclusion": "success",
        }

    provider = GitHubPullRequestProvider(
        repository_full_name="acme/repo",
        token="token",
        sender=sender,
    )

    result = await provider.report_check_run(
        name="AI Orchestrator",
        head_sha="abc123",
        status=CheckRunStatus.COMPLETED,
        conclusion=CheckRunConclusion.SUCCESS,
        summary="Workflow passed reviewer and tests.",
        details_url="https://orchestrator.example/workflows/1",
    )

    assert result.provider_id == "99"
    assert result.url == "https://github.com/acme/repo/runs/99"
    assert calls == [
        (
            "POST",
            "https://api.github.com/repos/acme/repo/check-runs",
            {
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer token",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            {
                "name": "AI Orchestrator",
                "head_sha": "abc123",
                "status": "completed",
                "conclusion": "success",
                "details_url": "https://orchestrator.example/workflows/1",
                "output": {
                    "title": "AI Orchestrator",
                    "summary": "Workflow passed reviewer and tests.",
                },
            },
        )
    ]
