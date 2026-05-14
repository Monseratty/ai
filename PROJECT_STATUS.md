# AI Software Engineering Orchestrator - статус проекта

## Краткое описание

Это backend-фундамент для production-grade системы оркестрации AI-агентов под software engineering workflows.

Главная архитектурная идея: Codex или другой coding model не является главным мозгом системы. Он работает как один из stateless worker-агентов внутри управляемого orchestration layer. Оркестратор отвечает за lifecycle, state, очереди, retries, reviewer loop, sandbox execution, git/PR flow, approvals, telemetry и безопасность.

Система проектировалась как более простая и расширяемая версия платформ класса Cursor background agents, Devin-style orchestration и Codex orchestration.

## Что реализовано

### Архитектура

- Clean architecture: `domain`, `application`, `infrastructure`, `interfaces`, `api`.
- Разделение ответственности между orchestrator, agents, repositories, sandbox, queue, git, telemetry и API.
- Typed domain models для workflow, task graph, artifacts, memory, execution history, approvals, review results и agent runs.
- Protocol/interfaces слой для замены инфраструктуры без переписывания бизнес-логики.
- Composition root для сборки API и worker runtime.

### Agent system

- Stateless planner, coder, tester и reviewer agent boundaries.
- System prompts вынесены в версионируемые prompt specs.
- Pydantic v2 input/output schemas для structured JSON.
- OpenAI Agents SDK adapter с structured output boundary.
- Retry при некорректной agent-схеме.
- Отдельная модель на роль: planner, coder, tester, reviewer.
- Deterministic fake agent backend для локальной разработки и тестов.

### Orchestration workflow

Реализован основной workflow:

1. User task.
2. Planner декомпозирует задачу.
3. Tasks попадают в очередь.
4. Coder выполняет coding phase.
5. Tester валидирует результат.
6. Reviewer обязательно проверяет результат.
7. При reject/request fixes создается bounded feedback loop.
8. При approve workflow может перейти к commit/PR flow.

Оркестратор также поддерживает:

- dependency-aware scheduling;
- bounded retries;
- task claiming для защиты от повторного исполнения;
- workflow cancel;
- manual task execution;
- manual task retry;
- success/failure transitions;
- сохранение execution history.

### Reviewer loop

Reviewer является обязательной фазой после coding/testing. В review contract заложены проверки:

- architecture consistency;
- typing;
- style;
- security;
- performance;
- hallucinated APIs;
- broken imports;
- test coverage.

Reviewer может вернуть:

- `approve`;
- `reject`;
- `request_fixes`.

### State / Memory

Подготовлен Postgres-oriented persistence layer:

- workflows;
- tasks;
- task dependencies;
- artifacts;
- agent runs;
- review results;
- memory records;
- execution history;
- approval gates.

Memory layer включает:

- short-term memory;
- long-term memory;
- vector memory abstraction;
- artifact memory;
- execution summaries.

### Queue / Worker

- Celery application boundary.
- Celery task queue adapter.
- Worker execution entrypoint.
- Worker-safe execution path: worker не исполняет задачи, которые уже не находятся в `queued`.

### Sandbox / Tool execution

- Docker sandbox executor.
- Изолированные workspace-директории на workflow/task.
- Sandbox policy:
  - command allowlist;
  - network disabled by default;
  - timeout limits;
  - CPU/memory/process limits;
  - явный workspace mount;
  - отсутствие доступа к secrets.
- Tool execution service с permission checks.
- Результаты tool execution сохраняются как artifacts.
- Non-zero tool execution переводит задачу в failure до reviewer approval.

### Git / PR integration

- GitPython service:
  - create branch;
  - diff generation;
  - commit;
  - rollback.
- Commit-on-success workflow hook.
- Rollback при commit failure.
- Approval-gated pull request service.
- GitHub REST PR provider.
- Composite git service: local git operations + configurable PR provider.

### API

FastAPI application factory и endpoints:

- create workflow;
- list workflows;
- get workflow snapshot;
- list artifacts;
- list execution history;
- manually execute task;
- retry task;
- cancel workflow;
- create approval gate;
- list approvals;
- approve gate;
- reject gate.

Также добавлены:

- optional bearer token auth;
- in-memory rate limiting для single-process local mode;
- Redis-backed distributed rate limiting для multi-instance deployment;
- API dependency wiring.

### Telemetry / Observability

- Backend-neutral telemetry interface.
- Structured logging telemetry.
- In-memory telemetry для тестов.
- OpenTelemetry adapter.
- Метрики workflow/task lifecycle.
- Failure/retry tracking через execution history.

### Security

- Tool permission system.
- Execution policies.
- Approval gates.
- Sandbox isolation.
- Optional API token auth.
- Rate limit boundary.
- Документация по security model.

### Tests

Текущая локальная проверка:

```text
73 passed, 5 skipped
```

Покрыты:

- unit tests;
- orchestration tests;
- agent contract tests;
- API contract tests;
- sandbox tests;
- git/PR tests;
- telemetry tests;
- opt-in live integration scaffolding.

Skipped tests ожидаемы без optional runtime dependencies или live-сервисов.

## Как запускать локально

1. Подготовить окружение:

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

2. Поднять инфраструктуру:

```bash
docker compose up -d postgres redis
```

3. Применить миграции:

```bash
alembic upgrade head
```

4. Проверить проект:

```bash
pytest tests -q
python -m compileall -q src tests/integration
```

5. Запустить API:

```bash
uvicorn ai_orchestrator.api.app:app --reload
```

6. Запустить worker:

```bash
celery -A ai_orchestrator.infrastructure.queue.worker worker --loglevel=info
```

7. Создать workflow:

```bash
curl -X POST http://127.0.0.1:8000/workflows \
  -H "content-type: application/json" \
  -d '{"user_task":"Add a typed endpoint with tests and docs"}'
```

## Основные environment variables

```bash
AIO_AGENT_BACKEND=fake
AIO_AGENT_BACKEND=openai
AIO_OPENAI_MODEL=gpt-5.2
AIO_PLANNER_MODEL=...
AIO_CODER_MODEL=...
AIO_TESTER_MODEL=...
AIO_REVIEWER_MODEL=...

AIO_PULL_REQUEST_PROVIDER=local
AIO_PULL_REQUEST_PROVIDER=github
AIO_GITHUB_REPOSITORY=owner/name
AIO_GITHUB_TOKEN=...

AIO_API_TOKEN=...
AIO_API_RATE_LIMIT_BACKEND=memory
AIO_API_RATE_LIMIT_BACKEND=redis
AIO_API_RATE_LIMIT_PER_MINUTE=60
AIO_TELEMETRY_BACKEND=logging
AIO_TELEMETRY_BACKEND=opentelemetry
```

## Что осталось

### Runtime validation

- Установить полный runtime dependency set в чистом Python 3.12 окружении.
- Прогнать live Postgres integration tests.
- Прогнать Redis/Celery integration tests.
- Прогнать Docker sandbox integration tests.
- Исправить проблемы, которые проявятся только при реальных сервисах.

### Production hardening

- Добавить полноценную operator identity/auth модель.
- Добавить secrets manager integration.
- Настроить JSON log formatter.
- Настроить production OpenTelemetry exporter.
- Добавить dashboard examples: latency, failure rate, retry count, reviewer rejection rate.

### GitHub / PR operations

- Добавить push orchestration перед GitHub PR creation.
- Добавить branch naming policy на workflow.
- Добавить PR status synchronization.
- Добавить GitHub check-run/status reporting.

### Agent tooling

- Расширить tool registry за пределы command execution.
- Добавить typed tool permissions по agent role и task kind.
- Добавить approval gates для privileged tools.
- Расширить reviewer finding schemas и аналитику.

### UI

Backend сейчас готовится как API-first платформа. UI лучше делать следующим этапом после runtime validation:

- workflow dashboard;
- task graph;
- agent run details;
- artifacts/logs/diffs;
- approval controls;
- PR status.

## Оценка готовности

Текущая оценка: примерно 89%.

Оставшиеся 11% - это в основном live integration, production hardening, расширение GitHub flow и UI.
