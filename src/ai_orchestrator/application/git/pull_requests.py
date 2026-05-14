from __future__ import annotations

from uuid import UUID

from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.interfaces.git import GitService, PullRequestResult


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
        return await self._git.open_pull_request(
            title=title,
            body=body,
            branch_name=branch_name,
            base_ref=base_ref,
        )
