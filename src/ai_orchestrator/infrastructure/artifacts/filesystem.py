from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from ai_orchestrator.domain.models.artifact import Artifact
from ai_orchestrator.interfaces.artifacts import ArtifactStore


class FilesystemArtifactStore(ArtifactStore):
    def __init__(self, root: Path) -> None:
        self._root = root

    async def write_text(
        self,
        *,
        workflow_id: UUID,
        task_id: UUID | None,
        kind: str,
        filename: str,
        content: str,
    ) -> Artifact:
        safe_filename = self._validate_filename(filename)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        relative_path = self._relative_path(workflow_id, task_id, content_hash, safe_filename)
        absolute_path = self._root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(content, encoding="utf-8")
        return Artifact(
            workflow_id=workflow_id,
            task_id=task_id,
            kind=kind,
            path=relative_path.as_posix(),
            content_hash=content_hash,
            metadata={"filename": safe_filename, "storage": "filesystem"},
        )

    def _relative_path(
        self,
        workflow_id: UUID,
        task_id: UUID | None,
        content_hash: str,
        filename: str,
    ) -> Path:
        if task_id is None:
            return Path("workflows") / str(workflow_id) / "artifacts" / content_hash / filename
        return (
            Path("workflows")
            / str(workflow_id)
            / "tasks"
            / str(task_id)
            / "artifacts"
            / content_hash
            / filename
        )

    def _validate_filename(self, filename: str) -> str:
        path = Path(filename)
        if path.name != filename or filename in {"", ".", ".."}:
            raise ValueError("Artifact filename must be a plain filename without path segments.")
        return filename
