from __future__ import annotations

from collections.abc import Awaitable, Callable

from ai_orchestrator.interfaces.git import PullRequestResult

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
            response = await client.request(method, url, headers=headers, json=json)
        if response.status_code >= 400:
            raise GitHubPullRequestError(
                f"GitHub PR creation failed with status {response.status_code}: {response.text}"
            )
        return response.json()
