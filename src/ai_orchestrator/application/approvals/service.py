from __future__ import annotations

from uuid import UUID

from ai_orchestrator.domain.enums import ApprovalStatus
from ai_orchestrator.domain.models.approval import ApprovalGate
from ai_orchestrator.interfaces.repositories import ApprovalRepository


class ApprovalService:
    def __init__(self, approvals: ApprovalRepository) -> None:
        self._approvals = approvals

    async def request_approval(
        self, *, workflow_id: UUID, gate_type: str, requested_action: dict
    ) -> ApprovalGate:
        gate = ApprovalGate(
            workflow_id=workflow_id,
            gate_type=gate_type,
            requested_action=requested_action,
        )
        await self._approvals.add(gate)
        return gate

    async def approve(self, gate_id: UUID, decided_by: str) -> ApprovalGate:
        gate = (await self._approvals.get(gate_id)).approve(decided_by)
        await self._approvals.update(gate)
        return gate

    async def reject(self, gate_id: UUID, decided_by: str) -> ApprovalGate:
        gate = (await self._approvals.get(gate_id)).reject(decided_by)
        await self._approvals.update(gate)
        return gate

    async def is_approved(self, gate_id: UUID) -> bool:
        gate = await self._approvals.get(gate_id)
        return gate.status is ApprovalStatus.APPROVED

    async def list_for_workflow(self, workflow_id: UUID) -> list[ApprovalGate]:
        return await self._approvals.list_by_workflow(workflow_id)
