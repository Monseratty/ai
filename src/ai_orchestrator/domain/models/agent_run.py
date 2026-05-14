from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.enums import AgentType
from ai_orchestrator.domain.models.common import new_id, utc_now


class AgentRun(BaseModel):
    id: UUID = Field(default_factory=new_id)
    workflow_id: UUID
    task_id: UUID | None = None
    agent_type: AgentType
    model: str
    status: str
    input: dict
    output: dict | None = None
    error: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None

