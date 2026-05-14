from __future__ import annotations

import pytest

from ai_orchestrator.infrastructure.queue.worker import (
    create_orchestrator_for_worker,
    register_worker_tasks,
)


def test_worker_factory_requires_production_composition() -> None:
    with pytest.raises(RuntimeError, match="production composition root"):
        create_orchestrator_for_worker()


def test_worker_task_registration_requires_celery_dependency_when_called() -> None:
    celery = pytest.importorskip("celery")
    assert celery is not None
    register_worker_tasks()
