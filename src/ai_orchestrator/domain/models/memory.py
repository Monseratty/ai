from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.models.common import new_id, utc_now


class MemoryRecord(BaseModel):
    id: UUID = Field(default_factory=new_id)
    workflow_id: UUID | None = None
    scope: str
    kind: str
    content: str
    embedding_ref: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

