from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.enums import TaskKind, TaskStatus
from ai_orchestrator.domain.models.common import new_id, utc_now


class Task(BaseModel):
    id: UUID = Field(default_factory=new_id)
    workflow_id: UUID
    parent_task_id: UUID | None = None
    kind: TaskKind
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 100
    attempt_count: int = 0
    max_attempts: int = 3
    input: dict = Field(default_factory=dict)
    output: dict | None = None
    dependency_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def with_status(self, status: TaskStatus) -> Task:
        return self.model_copy(update={"status": status, "updated_at": utc_now()})

    def with_output(self, output: dict) -> Task:
        return self.model_copy(update={"output": output, "updated_at": utc_now()})

