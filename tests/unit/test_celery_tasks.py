from __future__ import annotations

from uuid import uuid4

from ai_orchestrator.infrastructure.queue.tasks import parse_task_id


def test_parse_task_id_rejects_invalid_uuid() -> None:
    try:
        parse_task_id("not-a-uuid")
    except ValueError as exc:
        assert "Invalid task id" in str(exc)
    else:
        raise AssertionError("Expected invalid UUID to be rejected.")


def test_parse_task_id_accepts_uuid_string() -> None:
    task_id = uuid4()

    assert parse_task_id(str(task_id)) == task_id
