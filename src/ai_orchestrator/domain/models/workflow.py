from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.enums import WorkflowStatus
from ai_orchestrator.domain.models.common import new_id, utc_now


class Workflow(BaseModel):
    id: UUID = Field(default_factory=new_id)
    user_task: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    branch_name: str | None = None
    base_ref: str = "main"
    max_retries: int = 3
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def with_status(self, status: WorkflowStatus) -> Workflow:
        return self.model_copy(update={"status": status, "updated_at": utc_now()})

