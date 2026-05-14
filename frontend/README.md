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
