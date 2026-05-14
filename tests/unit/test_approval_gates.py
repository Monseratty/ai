from __future__ import annotations

import asyncio

from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.domain.enums import ApprovalStatus
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.testing.fakes import InMemoryApprovalRepository


def test_sensitive_action_requires_pending_approval_gate() -> None:
    asyncio.run(_assert_sensitive_action_requires_pending_gate())


async def _assert_sensitive_action_requires_pending_gate() -> None:
    repository = InMemoryApprovalRepository()
    service = ApprovalService(repository)
    workflow = Workflow(user_task="Open PR")

    gate = await service.request_approval(
        workflow_id=workflow.id,
        gate_type="pull_request",
        requested_action={"branch": "codex/example"},
    )

    assert gate.status is ApprovalStatus.PENDING
    assert await service.is_approved(gate.id) is False

    approved = await service.approve(gate.id, decided_by="operator")

    assert approved.status is ApprovalStatus.APPROVED
    assert await service.is_approved(gate.id) is True
