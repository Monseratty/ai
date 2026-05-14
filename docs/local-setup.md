# Local Setup

## Requirements

- Python 3.12
- Docker
- Docker Compose
- Postgres and Redis via `docker-compose.yml`

## Commands

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d postgres redis
alembic upgrade head
pytest tests -q
uvicorn ai_orchestrator.api.app:app --reload
```

## Live Integration Tests

By default, live integration tests are skipped. To run them, install dependencies, start services, and opt in:

```bash
docker compose up -d postgres redis
alembic upgrade head
AIO_RUN_INTEGRATION_TESTS=1 pytest tests/integration -q
```

Docker sandbox integration also requires the Docker CLI and local image access.

## API Smoke Test

```bash
curl -X POST http://127.0.0.1:8000/workflows \
  -H 'content-type: application/json' \
  -d '{"user_task":"Add a typed health endpoint"}'
```

List workflows:

```bash
curl http://127.0.0.1:8000/workflows
```

Inspect a workflow:

```bash
curl http://127.0.0.1:8000/workflows/<workflow_id>
curl http://127.0.0.1:8000/workflows/<workflow_id>/artifacts
curl http://127.0.0.1:8000/workflows/<workflow_id>/history
```

Create and decide an approval gate:

```bash
curl -X POST http://127.0.0.1:8000/approvals \
  -H 'content-type: application/json' \
  -d '{"workflow_id":"<workflow_id>","gate_type":"pull_request","requested_action":{"branch":"codex/example"}}'

curl -X POST http://127.0.0.1:8000/approvals/<gate_id>/approve \
  -H 'content-type: application/json' \
  -d '{"decided_by":"operator"}'
```

## Worker

The Celery worker module is available at:

```bash
celery -A ai_orchestrator.infrastructure.queue.worker worker --loglevel=info
```

The worker uses the same composition root as the API. Set `AIO_AGENT_BACKEND=openai` for real OpenAI Agents SDK execution; keep `fake` for deterministic local smoke tests.

Per-agent model overrides are available through:

```bash
AIO_PLANNER_MODEL=...
AIO_CODER_MODEL=...
AIO_TESTER_MODEL=...
AIO_REVIEWER_MODEL=...
```
