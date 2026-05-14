from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.enums import ApprovalStatus
from ai_orchestrator.domain.models.common import new_id, utc_now


class ApprovalGate(BaseModel):
    id: UUID = Field(default_factory=new_id)
    workflow_id: UUID
    gate_type: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_action: dict
    decided_by: str | None = None
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)

    def approve(self, decided_by: str) -> ApprovalGate:
        return self.model_copy(
            update={
                "status": ApprovalStatus.APPROVED,
                "decided_by": decided_by,
                "decided_at": utc_now(),
            }
        )

    def reject(self, decided_by: str) -> ApprovalGate:
        return self.model_copy(
            update={
                "status": ApprovalStatus.REJECTED,
                "decided_by": decided_by,
                "decided_at": utc_now(),
            }
        )
