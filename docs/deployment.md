# Deployment Guide

## Services

- API service: FastAPI application.
- Worker service: Celery workers executing orchestration tasks.
- Postgres: canonical state and memory records.
- Redis: Celery broker and result backend.
- Docker runtime: isolated sandbox execution.

## Database Setup

Apply the initial schema before starting API or workers:

```bash
alembic upgrade head
```

The application setting uses SQLAlchemy's async `postgresql+asyncpg://...` form.

## Production Requirements

- Use managed Postgres with backups and point-in-time recovery.
- Use managed Redis or a hardened Redis deployment.
- Run API and workers with separate service identities.
- Do not mount secrets into sandbox containers.
- Set network defaults to deny for sandbox jobs.
- Add centralized logs, traces, and metrics.
- Configure rate limits at gateway and application levels.
- Provide a production composition root that creates Postgres repositories, `CeleryTaskQueue`, artifact storage, `OpenAIAgentsSDKClient`, telemetry, sandbox, and git services.
- Set `AIO_AGENT_BACKEND=openai` for production model execution.
- Run `AIO_RUN_INTEGRATION_TESTS=1 pytest tests/integration -q` against the deployment substrate before enabling workers.
- Use `AIO_TELEMETRY_BACKEND=opentelemetry` for production metrics/traces.
- Set `AIO_API_RATE_LIMIT_PER_MINUTE` according to expected operator/API traffic.

## GitHub Pull Requests

Set these variables to use the GitHub PR provider:

```bash
AIO_PULL_REQUEST_PROVIDER=github
AIO_GITHUB_REPOSITORY=owner/name
AIO_GITHUB_TOKEN=...
```

Pull request creation remains approval-gated by `PullRequestService`.

## Migration Path

The initial queue implementation uses Celery. Temporal can be introduced by implementing the `TaskQueue` protocol and moving orchestration state transitions into Temporal activities while keeping domain and agent contracts unchanged.
