from __future__ import annotations

import asyncio

from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.testing.fakes import InMemoryApprovalRepository


def test_approval_service_lists_workflow_gates() -> None:
    asyncio.run(_assert_approval_service_lists_workflow_gates())


async def _assert_approval_service_lists_workflow_gates() -> None:
    repository = InMemoryApprovalRepository()
    service = ApprovalService(repository)
    workflow = Workflow(user_task="Open PR")

    gate = await service.request_approval(
        workflow_id=workflow.id,
        gate_type="pull_request",
        requested_action={"branch": "codex/example"},
    )

    assert [item.id for item in await service.list_for_workflow(workflow.id)] == [gate.id]
