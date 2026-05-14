# Operations Runbook

## Start Local Stack

```bash
cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
uvicorn ai_orchestrator.api.app:app --reload
celery -A ai_orchestrator.infrastructure.queue.worker worker --loglevel=info
```

## Health Checks

```bash
curl http://127.0.0.1:8000/health
pytest tests -q
AIO_RUN_INTEGRATION_TESTS=1 pytest tests/integration -q
```

## Common Failures

- `task.claim_skipped`: a worker retried a task that was no longer queued. This is usually safe.
- `task.tool_failed`: sandbox command returned non-zero. Inspect workflow artifacts.
- `git.commit_failed`: commit failed and rollback was attempted. Inspect repository status.
- Missing API auth: send `Authorization: Bearer <token>` when `AIO_API_TOKEN` is configured.

## Production Checklist

- `AIO_AGENT_BACKEND=openai`
- `AIO_PULL_REQUEST_PROVIDER=github`
- `AIO_GITHUB_REPOSITORY=owner/name`
- `AIO_GITHUB_TOKEN` set from secret manager
- `AIO_API_TOKEN` set from secret manager
- `AIO_TELEMETRY_BACKEND=opentelemetry`
- sandbox network disabled unless explicitly approved
- live integration tests passed
