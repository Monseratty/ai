from __future__ import annotations

import os

import pytest

pytest.importorskip("celery")
pytest.importorskip("redis")


def require_integration() -> None:
    if os.getenv("AIO_RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Set AIO_RUN_INTEGRATION_TESTS=1 to run live integration tests.")


def test_celery_dependencies_are_available_for_worker_runtime() -> None:
    require_integration()
    from ai_orchestrator.infrastructure.queue.celery_app import celery_app

    assert celery_app.main == "ai_orchestrator"
