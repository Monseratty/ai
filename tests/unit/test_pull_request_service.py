from __future__ import annotations

import asyncio

from ai_orchestrator.application.git.pull_requests import PullRequestService
from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.testing.fakes import FakeGitService, InMemoryApprovalRepository
from ai_orchestrator.interfaces.git import CheckRunConclusion, CheckRunStatus


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


def test_pull_request_service_reports_check_run_through_git_boundary() -> None:
    asyncio.run(_assert_pull_request_service_reports_check_run_through_git_boundary())


async def _assert_pull_request_service_reports_check_run_through_git_boundary() -> None:
    git = FakeGitService()
    service = PullRequestService(
        git=git,
        approvals=ApprovalService(InMemoryApprovalRepository()),
    )

    result = await service.report_check_run(
        name="AI Orchestrator",
        head_sha="abc123",
        status=CheckRunStatus.COMPLETED,
        conclusion=CheckRunConclusion.SUCCESS,
        summary="Passed reviewer and tests.",
        details_url="https://orchestrator.example/workflows/1",
    )

    assert result.provider_id == "fake:1"
    assert git.check_runs == [
        (
            "AI Orchestrator",
            "abc123",
            CheckRunStatus.COMPLETED,
            CheckRunConclusion.SUCCESS,
            "Passed reviewer and tests.",
            "https://orchestrator.example/workflows/1",
        )
    ]
