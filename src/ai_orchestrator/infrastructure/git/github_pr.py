from __future__ import annotations

from collections.abc import Awaitable, Callable

from ai_orchestrator.interfaces.git import (
    CheckRunConclusion,
    CheckRunResult,
    CheckRunStatus,
    PullRequestResult,
    PullRequestState,
    PullRequestStatus,
)

HttpSender = Callable[[str, str, dict, dict], Awaitable[dict]]


class GitHubPullRequestError(RuntimeError):
    """Raised when GitHub pull request creation fails."""


class GitHubPullRequestProvider:
    def __init__(
        self,
        *,
        repository_full_name: str,
        token: str,
        sender: HttpSender | None = None,
    ) -> None:
        if "/" not in repository_full_name:
            raise ValueError("repository_full_name must use 'owner/name' format.")
        if not token:
            raise ValueError("GitHub token is required.")
        self._repository_full_name = repository_full_name
        self._token = token
        self._sender = sender

    async def open_pull_request(
        self,
        *,
        title: str,
        body: str,
        branch_name: str,
        base_ref: str = "main",
    ) -> PullRequestResult:
        payload = {
            "title": title,
            "body": body,
            "head": branch_name,
            "base": base_ref,
            "draft": True,
        }
        response = await self._send(
            "POST",
            f"https://api.github.com/repos/{self._repository_full_name}/pulls",
            self._headers(),
            payload,
        )
        return PullRequestResult(
            url=response["html_url"],
            number=response.get("number"),
            is_draft=response.get("draft", True),
        )

    async def get_pull_request_status(self, number: int) -> PullRequestStatus:
        response = await self._send(
            "GET",
            f"https://api.github.com/repos/{self._repository_full_name}/pulls/{number}",
            self._headers(),
            {},
        )
        is_merged = bool(response.get("merged", False))
        state = PullRequestState.MERGED if is_merged else PullRequestState(response["state"])
        return PullRequestStatus(
            number=response["number"],
            url=response["html_url"],
            state=state,
            is_draft=response.get("draft", False),
            is_merged=is_merged,
            head_ref=response["head"]["ref"],
            head_sha=response["head"].get("sha"),
            base_ref=response["base"]["ref"],
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
        payload = {
            "name": name,
            "head_sha": head_sha,
            "status": status.value,
            "output": {
                "title": name,
                "summary": summary,
            },
        }
        if conclusion is not None:
            payload["conclusion"] = conclusion.value
        if details_url is not None:
            payload["details_url"] = details_url

        response = await self._send(
            "POST",
            f"https://api.github.com/repos/{self._repository_full_name}/check-runs",
            self._headers(),
            payload,
        )
        return CheckRunResult(
            provider_id=str(response["id"]),
            url=response["html_url"],
        )

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _send(self, method: str, url: str, headers: dict, json: dict) -> dict:
        if self._sender is not None:
            return await self._sender(method, url, headers, json)
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("Install httpx to use GitHubPullRequestProvider.") from exc

        async with httpx.AsyncClient(timeout=30.0) as client:
            kwargs = {"headers": headers}
            if json:
                kwargs["json"] = json
            response = await client.request(method, url, **kwargs)
        if response.status_code >= 400:
            raise GitHubPullRequestError(
                f"GitHub PR creation failed with status {response.status_code}: {response.text}"
            )
        return response.json()
