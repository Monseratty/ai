from __future__ import annotations

import asyncio

from ai_orchestrator.infrastructure.git.github_pr import GitHubPullRequestProvider


def test_github_pull_request_provider_posts_expected_payload() -> None:
    asyncio.run(_assert_github_pull_request_provider_posts_expected_payload())


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
