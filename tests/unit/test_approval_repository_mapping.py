from __future__ import annotations

from ai_orchestrator.domain.enums import ApprovalStatus
from ai_orchestrator.domain.models.approval import ApprovalGate
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.db.approval_repositories import (
    approval_gate_to_row,
    row_to_approval_gate,
)


def test_approval_gate_row_roundtrip_preserves_decision_metadata() -> None:
    workflow = Workflow(user_task="Open PR")
    gate = ApprovalGate(
        workflow_id=workflow.id,
        gate_type="pull_request",
        status=ApprovalStatus.APPROVED,
        requested_action={"branch": "codex/example"},
        decided_by="operator",
    )

    assert row_to_approval_gate(approval_gate_to_row(gate)) == gate
