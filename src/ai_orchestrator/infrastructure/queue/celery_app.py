from __future__ import annotations

from celery import Celery

from ai_orchestrator.config.settings import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "ai_orchestrator",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    app.conf.update(task_track_started=True, task_serializer="json", result_serializer="json")
    return app


celery_app = create_celery_app()

