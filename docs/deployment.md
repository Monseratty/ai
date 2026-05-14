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
- Set `AIO_API_RATE_LIMIT_BACKEND=redis` for horizontally scaled API deployments.
- Provide a production composition root that creates Postgres repositories, `CeleryTaskQueue`, artifact storage, `OpenAIAgentsSDKClient`, telemetry, sandbox, and git services.
- Set `AIO_AGENT_BACKEND=openai` for production model execution.
- Run `AIO_RUN_INTEGRATION_TESTS=1 pytest tests/integration -q` against the deployment substrate before enabling workers.
- Use `AIO_TELEMETRY_BACKEND=opentelemetry` for production metrics/traces.
- Set `AIO_API_RATE_LIMIT_PER_MINUTE` according to expected operator/API traffic.

## API Rate Limiting

Local development can use the default in-memory limiter:

```bash
AIO_API_RATE_LIMIT_BACKEND=memory
```

Production deployments with multiple API replicas should use Redis:

```bash
AIO_API_RATE_LIMIT_BACKEND=redis
AIO_REDIS_URL=redis://redis:6379/0
AIO_API_RATE_LIMIT_PER_MINUTE=120
```

The Redis limiter hashes client keys before storage so bearer tokens or raw identifiers are not written into Redis keys.

## GitHub Pull Requests

Set these variables to use the GitHub PR provider:

```bash
AIO_BRANCH_PREFIX=codex/
AIO_PULL_REQUEST_PROVIDER=github
AIO_GITHUB_REPOSITORY=owner/name
AIO_GITHUB_TOKEN=...
```

Workflow branches are generated from the configured prefix, a sanitized user-task slug, and the workflow id prefix. Pull request creation remains approval-gated by `PullRequestService`, and the branch is pushed before the GitHub PR provider is called.

Pull request status can be read through the API:

```bash
curl http://127.0.0.1:8000/pull-requests/7
```

## Migration Path

The initial queue implementation uses Celery. Temporal can be introduced by implementing the `TaskQueue` protocol and moving orchestration state transitions into Temporal activities while keeping domain and agent contracts unchanged.
