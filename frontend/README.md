# AI Orchestrator Console

Static operator UI for the FastAPI orchestration backend.

## Run

From the repository root:

```bash
python -m http.server 4173 -d frontend
```

Open:

```text
http://127.0.0.1:4173
```

Backend API should run separately:

```bash
uvicorn ai_orchestrator.api.app:app --reload
```

By default the backend uses `AIO_STATE_BACKEND=memory` and `AIO_QUEUE_BACKEND=memory`, so the console works without Postgres, Redis, or Celery. Git operations are also disabled by default with `AIO_GIT_ENABLED=false`, so UI workflow creation will not switch local branches. For persistent state and real git operations, set `AIO_STATE_BACKEND=postgres`, `AIO_QUEUE_BACKEND=celery`, set `AIO_GIT_ENABLED=true`, start Postgres/Redis, and run Alembic migrations.

The default backend CORS setting allows `http://127.0.0.1:4173` and `http://localhost:4173`.

The UI stores API base URL and optional bearer token in browser local storage. If the API is not reachable, it falls back to seeded demo data so the console remains inspectable.

## Supported Operations

- Create workflow.
- List workflows.
- Inspect workflow snapshot and task graph.
- Execute or retry tasks.
- Inspect execution history.
- View and decide approval gates.
- Read GitHub pull request status.
- Report GitHub check-run result.
