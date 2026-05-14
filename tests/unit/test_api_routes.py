from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from ai_orchestrator.api.deps import get_orchestrator, get_pull_request_service  # noqa: E402
from ai_orchestrator.api.app import create_app
from ai_orchestrator.application.orchestrator.service import OrchestratorService  # noqa: E402
from ai_orchestrator.interfaces.git import (  # noqa: E402
    CheckRunConclusion,
    CheckRunResult,
    CheckRunStatus,
    PullRequestState,
    PullRequestStatus,
)
from ai_orchestrator.infrastructure.testing.fakes import (  # noqa: E402
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryExecutionEventRepository,
    InMemoryTaskQueue,
    InMemoryTaskRepository,
    InMemoryTelemetry,
    InMemoryWorkflowRepository,
)


def create_test_client() -> TestClient:
    app = create_app()
    service = OrchestratorService(
        workflows=InMemoryWorkflowRepository(),
        tasks=InMemoryTaskRepository(),
        artifacts=InMemoryArtifactRepository(),
        queue=InMemoryTaskQueue(),
        agents=FakeAgentClient.approving_code_review(),
        telemetry=InMemoryTelemetry(),
        execution_events=InMemoryExecutionEventRepository(),
    )
    app.dependency_overrides[get_orchestrator] = lambda: service
    return TestClient(app)


def test_api_creates_and_reads_workflow_snapshot() -> None:
    client = create_test_client()

    created = client.post("/workflows", json={"user_task": "Build read endpoint"})

    assert created.status_code == 202
    workflow_id = created.json()["id"]

    fetched = client.get(f"/workflows/{workflow_id}")

    assert fetched.status_code == 200
    body = fetched.json()
    assert body["workflow"]["id"] == workflow_id
    assert len(body["tasks"]) == 2


def test_api_exposes_workflow_observability_resources() -> None:
    client = create_test_client()
    created = client.post("/workflows", json={"user_task": "Expose observability"})
    workflow_id = created.json()["id"]

    workflows = client.get("/workflows")
    artifacts = client.get(f"/workflows/{workflow_id}/artifacts")
    history = client.get(f"/workflows/{workflow_id}/history")

    assert workflows.status_code == 200
    assert workflows.json()[0]["id"] == workflow_id
    assert artifacts.status_code == 200
    assert history.status_code == 200
    assert [event["event_type"] for event in history.json()] == [
        "workflow.created",
        "workflow.planned",
    ]


def test_api_supports_manual_task_execute_retry_and_workflow_cancel() -> None:
    client = create_test_client()
    created = client.post("/workflows", json={"user_task": "Control workflow"})
    workflow_id = created.json()["id"]
    snapshot = client.get(f"/workflows/{workflow_id}").json()
    task_id = snapshot["tasks"][0]["id"]
    dependent_task_id = snapshot["tasks"][1]["id"]

    executed = client.post(f"/workflows/tasks/{task_id}/execute")
    cancelled = client.post(f"/workflows/{workflow_id}/cancel")
    retry = client.post(f"/workflows/tasks/{dependent_task_id}/retry")

    assert executed.status_code == 200
    assert executed.json()["task_id"] == task_id
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert retry.status_code == 200
    assert retry.json()["status"] == "queued"


def test_api_reads_pull_request_status() -> None:
    app = create_app()

    class FakePullRequestService:
        async def get_pull_request_status(self, number: int) -> PullRequestStatus:
            return PullRequestStatus(
                number=number,
                url=f"https://github.com/acme/repo/pull/{number}",
                state=PullRequestState.OPEN,
                is_draft=False,
                is_merged=False,
                head_ref="codex/work",
                head_sha="abc123",
                base_ref="main",
            )

        async def report_check_run(
            self,
            *,
            name: str,
            head_sha: str,
            status: CheckRunStatus,
            conclusion: CheckRunConclusion | None = None,
            summary: str,
            details_url: str | None = None,
        ) -> CheckRunResult:
            return CheckRunResult(provider_id="99", url="https://github.com/acme/repo/runs/99")

    app.dependency_overrides[get_pull_request_service] = lambda: FakePullRequestService()
    client = TestClient(app)

    response = client.get("/pull-requests/7")

    assert response.status_code == 200
    assert response.json() == {
        "number": 7,
        "url": "https://github.com/acme/repo/pull/7",
        "state": "open",
        "is_draft": False,
        "is_merged": False,
        "head_ref": "codex/work",
        "head_sha": "abc123",
        "base_ref": "main",
    }


def test_api_reports_check_run() -> None:
    app = create_app()

    class FakePullRequestService:
        async def report_check_run(
            self,
            *,
            name: str,
            head_sha: str,
            status: CheckRunStatus,
            conclusion: CheckRunConclusion | None = None,
            summary: str,
            details_url: str | None = None,
        ) -> CheckRunResult:
            return CheckRunResult(provider_id="99", url="https://github.com/acme/repo/runs/99")

    app.dependency_overrides[get_pull_request_service] = lambda: FakePullRequestService()
    client = TestClient(app)

    response = client.post(
        "/pull-requests/check-runs",
        json={
            "name": "AI Orchestrator",
            "head_sha": "abc123",
            "status": "completed",
            "conclusion": "success",
            "summary": "Passed reviewer and tests.",
            "details_url": "https://orchestrator.example/workflows/1",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "provider_id": "99",
        "url": "https://github.com/acme/repo/runs/99",
    }
