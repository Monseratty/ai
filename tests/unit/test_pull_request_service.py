from __future__ import annotations

import asyncio

from ai_orchestrator.application.git.pull_requests import PullRequestService
from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.testing.fakes import FakeGitService, InMemoryApprovalRepository


def test_pull_request_service_requires_approved_gate_before_opening_pr() -> None:
    asyncio.run(_assert_pull_request_service_requires_approved_gate_before_opening_pr())


async def _assert_pull_request_service_requires_approved_gate_before_opening_pr() -> None:
    approvals = ApprovalService(InMemoryApprovalRepository())
    git = FakeGitService()
    service = PullRequestService(git=git, approvals=approvals)
    workflow = Workflow(user_task="Open PR")
    gate = await approvals.request_approval(
        workflow_id=workflow.id,
        gate_type="pull_request",
        requested_action={"branch": "codex/work"},
    )

    try:
        await service.open_pull_request(
            approval_gate_id=gate.id,
            title="Complete workflow",
            body="Summary",
            branch_name="codex/work",
            base_ref="main",
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("Expected pending gate to block PR creation.")

    await approvals.approve(gate.id, decided_by="operator")
    result = await service.open_pull_request(
        approval_gate_id=gate.id,
        title="Complete workflow",
        body="Summary",
        branch_name="codex/work",
        base_ref="main",
    )

    assert result.url == "local://pull-request/codex/work"
    assert git.pushes == [("codex/work", "origin")]
    assert git.pull_requests == [("Complete workflow", "Summary", "codex/work", "main")]


def test_pull_request_service_reads_status_through_git_boundary() -> None:
    asyncio.run(_assert_pull_request_service_reads_status_through_git_boundary())


async def _assert_pull_request_service_reads_status_through_git_boundary() -> None:
    service = PullRequestService(
        git=FakeGitService(),
        approvals=ApprovalService(InMemoryApprovalRepository()),
    )

    status = await service.get_pull_request_status(7)

    assert status.number == 7
    assert status.url == "local://pull-request/7"
