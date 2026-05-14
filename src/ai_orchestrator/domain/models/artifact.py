from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.enums import ArtifactKind
from ai_orchestrator.domain.models.common import new_id, utc_now


class Artifact(BaseModel):
    id: UUID = Field(default_factory=new_id)
    workflow_id: UUID
    task_id: UUID | None = None
    kind: ArtifactKind | str
    path: str | None = None
    content_hash: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

