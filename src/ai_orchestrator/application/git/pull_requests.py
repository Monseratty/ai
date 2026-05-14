from __future__ import annotations

from uuid import UUID

from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.interfaces.git import (
    CheckRunConclusion,
    CheckRunResult,
    CheckRunStatus,
    GitService,
    PullRequestResult,
    PullRequestStatus,
)


class PullRequestService:
    def __init__(self, *, git: GitService, approvals: ApprovalService) -> None:
        self._git = git
        self._approvals = approvals

    async def open_pull_request(
        self,
        *,
        approval_gate_id: UUID,
        title: str,
        body: str,
        branch_name: str,
        base_ref: str = "main",
    ) -> PullRequestResult:
        if not await self._approvals.is_approved(approval_gate_id):
            raise PermissionError("Pull request creation requires an approved approval gate.")
        await self._git.push(branch_name, remote="origin")
        return await self._git.open_pull_request(
            title=title,
            body=body,
            branch_name=branch_name,
            base_ref=base_ref,
        )

    async def get_pull_request_status(self, number: int) -> PullRequestStatus:
        return await self._git.get_pull_request_status(number)

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
        return await self._git.report_check_run(
            name=name,
            head_sha=head_sha,
            status=status,
            conclusion=conclusion,
            summary=summary,
            details_url=details_url,
        )
