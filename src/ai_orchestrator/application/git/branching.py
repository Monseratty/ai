from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BranchNamingPolicy:
    prefix: str = "codex/"
    max_slug_length: int = 48

    def for_workflow(self, *, workflow_id: UUID, user_task: str) -> str:
        slug = self._slugify(user_task) or "workflow"
        return f"{self.prefix}{slug}-{workflow_id.hex[:8]}"

    def _slugify(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        normalized = re.sub(r"-+", "-", normalized)
        return normalized[: self.max_slug_length].strip("-")
