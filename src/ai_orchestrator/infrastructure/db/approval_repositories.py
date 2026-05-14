from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_orchestrator.domain.enums import ApprovalStatus
from ai_orchestrator.domain.models.approval import ApprovalGate
from ai_orchestrator.infrastructure.db.models import ApprovalGateRow


def approval_gate_to_row(gate: ApprovalGate) -> ApprovalGateRow:
    return ApprovalGateRow(
        id=gate.id,
        workflow_id=gate.workflow_id,
        gate_type=gate.gate_type,
        status=gate.status.value,
        requested_action=gate.requested_action,
        decided_by=gate.decided_by,
        decided_at=gate.decided_at,
        created_at=gate.created_at,
    )


def row_to_approval_gate(row: ApprovalGateRow) -> ApprovalGate:
    return ApprovalGate(
        id=row.id,
        workflow_id=row.workflow_id,
        gate_type=row.gate_type,
        status=ApprovalStatus(row.status),
        requested_action=row.requested_action,
        decided_by=row.decided_by,
        decided_at=row.decided_at,
        created_at=row.created_at,
    )


class SqlAlchemyApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, gate: ApprovalGate) -> None:
        self._session.add(approval_gate_to_row(gate))

    async def get(self, gate_id: UUID) -> ApprovalGate:
        row = await self._session.get(ApprovalGateRow, gate_id)
        if row is None:
            raise KeyError(f"Approval gate {gate_id} not found.")
        return row_to_approval_gate(row)

    async def update(self, gate: ApprovalGate) -> None:
        await self._session.merge(approval_gate_to_row(gate))

    async def list_by_workflow(self, workflow_id: UUID) -> list[ApprovalGate]:
        result = await self._session.execute(
            select(ApprovalGateRow)
            .where(ApprovalGateRow.workflow_id == workflow_id)
            .order_by(ApprovalGateRow.created_at)
        )
        return [row_to_approval_gate(row) for row in result.scalars().all()]
