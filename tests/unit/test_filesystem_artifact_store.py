from __future__ import annotations

import asyncio
from uuid import uuid4

from ai_orchestrator.infrastructure.artifacts.filesystem import FilesystemArtifactStore


def test_filesystem_artifact_store_writes_content_addressed_artifact(tmp_path) -> None:
    asyncio.run(_assert_filesystem_artifact_store_writes_content_addressed_artifact(tmp_path))


async def _assert_filesystem_artifact_store_writes_content_addressed_artifact(tmp_path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    workflow_id = uuid4()
    task_id = uuid4()

    artifact = await store.write_text(
        workflow_id=workflow_id,
        task_id=task_id,
        kind="test_report",
        filename="pytest.txt",
        content="3 passed",
    )

    assert artifact.path is not None
    assert artifact.content_hash == "61affed06dc6ccb76520673de0b462156a4f4f1e0ed67cc6450fe0c2da8c5d07"
    assert (tmp_path / artifact.path).read_text() == "3 passed"
    assert artifact.metadata["filename"] == "pytest.txt"


def test_filesystem_artifact_store_rejects_path_traversal_filename(tmp_path) -> None:
    async def run() -> None:
        store = FilesystemArtifactStore(root=tmp_path)
        await store.write_text(
            workflow_id=uuid4(),
            task_id=None,
            kind="log",
            filename="../escape.txt",
            content="bad",
        )

    try:
        asyncio.run(run())
    except ValueError as exc:
        assert "filename" in str(exc)
    else:
        raise AssertionError("Expected path traversal filename to be rejected.")
