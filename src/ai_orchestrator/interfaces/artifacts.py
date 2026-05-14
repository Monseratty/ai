from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ai_orchestrator.domain.models.artifact import Artifact


class ArtifactStore(Protocol):
    async def write_text(
        self,
        *,
        workflow_id: UUID,
        task_id: UUID | None,
        kind: str,
        filename: str,
        content: str,
    ) -> Artifact: ...
