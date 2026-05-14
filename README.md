# AI Software Engineering Orchestrator

Production-grade skeleton for orchestrating AI agents across software engineering workflows.

Codex is treated as a coding worker behind the orchestration layer. The orchestrator owns state, lifecycle, retries, dependencies, reviewer gates, and tool policy enforcement.

## Capabilities

- Planner, coder, tester, reviewer, and documentation agent boundaries.
- Stateless structured agent contracts with Pydantic v2.
- OpenAI Agents SDK adapter with schema retry and per-agent model config.
- Mandatory reviewer loop after coding.
- Task graph and dependency-aware queueing.
- Persistent-state architecture for Postgres.
- Redis/Celery queue boundary.
- Docker sandbox execution boundary with resource policy checks.
- Sandbox workspace preparation and validation command service.
- Policy-checked tool execution layer for agent-requested sandbox commands.
- Agent/task-scoped tool permission policy.
- Idempotent worker task claiming with retry attempt tracking.
- GitPython integration boundary for branch, diff, commit, rollback, and PR creation.
- Commit-on-success workflow hook with rollback on commit failure.
- Workflow branch naming policy with configurable prefix.
- Approval-gated pull request service.
- Push orchestration before pull request creation.
- GitHub pull request provider.
- Pull request status synchronization boundary and API endpoint.
- GitHub check-run reporting boundary and API endpoint.
- Logging and OpenTelemetry telemetry backends.
- FastAPI API surface.
- Redis-backed distributed API rate limiting for multi-instance deployments.
- Workflow snapshot endpoint.
- Workflow list, artifacts, execution history, and approval endpoints.
- Structured telemetry boundary.
- Persistent execution history boundary.
- Approval gates for sensitive actions.
- Filesystem artifact storage for inline agent outputs.
- Celery queue adapter and worker registration boundary.
- Deterministic fakes for orchestration and contract tests.
- Opt-in live integration tests for Postgres, Redis/Celery, and Docker sandbox.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d postgres redis
alembic upgrade head
pytest tests -q
uvicorn ai_orchestrator.api.app:app --reload
```

Local state defaults to `AIO_STATE_BACKEND=memory` and `AIO_QUEUE_BACKEND=memory`, so the API works without Postgres, Redis, or Celery for UI testing. Git operations are disabled by default with `AIO_GIT_ENABLED=false`, so creating a workflow from the UI will not switch branches. Set `AIO_STATE_BACKEND=postgres`, `AIO_QUEUE_BACKEND=celery`, start Postgres/Redis, run migrations, and set `AIO_GIT_ENABLED=true` when you want persistent state and real branch/commit/PR operations.

## Operator UI

The static console lives in `frontend/`:

```bash
python -m http.server 4173 -d frontend
```

Open `http://127.0.0.1:4173` and point it at the FastAPI base URL.
The API allows this local console origin through `AIO_API_CORS_ORIGINS`.

## Architecture

See [docs/architecture.md](docs/architecture.md).
See [docs/runbook.md](docs/runbook.md) for operational commands and failure handling.

## Project Status

This is a production-grade foundation. It includes the core boundaries, domain model, orchestration loop, reviewer gate, bounded feedback loop, deterministic fakes, Postgres repository adapters, SQL migration, OpenAI Agents SDK adapter with schema retry, per-agent model config, Docker sandbox command construction, sandbox workspace preparation, policy-checked tool execution, idempotent worker task claiming, approval gates, execution history, filesystem artifact storage, Celery queue adapter, API observability endpoints, git commit/rollback flow, branch naming, approval-gated PR service, GitHub PR provider, PR status synchronization, GitHub check-run reporting, and tests.

Remaining production wiring:

- Run live integration tests in the target environment.

For production agent execution, set `AIO_AGENT_BACKEND=openai`. The default `fake` backend keeps local development deterministic.
For more than one API instance, set `AIO_API_RATE_LIMIT_BACKEND=redis` so rate limiting is shared through Redis instead of process memory.
