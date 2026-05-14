from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from ai_orchestrator.application.agents.schemas import (
    AgentInput,
    CoderOutput,
    PlannedTask,
    PlannerOutput,
    ReviewerFinding,
    ReviewerOutput,
    TesterOutput,
)
from ai_orchestrator.domain.enums import ReviewDecision, Severity, TaskKind
from ai_orchestrator.domain.models.approval import ApprovalGate
from ai_orchestrator.domain.models.execution import ExecutionEvent
from ai_orchestrator.domain.models.artifact import Artifact
from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.interfaces.git import CommitResult, PullRequestResult
from ai_orchestrator.domain.enums import TaskStatus


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self._workflows: dict[UUID, Workflow] = {}

    async def add(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    async def get(self, workflow_id: UUID) -> Workflow:
        return self._workflows[workflow_id]

    async def update(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    async def list_recent(self, limit: int = 50) -> list[Workflow]:
        return list(self._workflows.values())[-limit:]


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}

    async def add_many(self, tasks: list[Task]) -> None:
        for task in tasks:
            self._tasks[task.id] = task

    async def add(self, task: Task) -> None:
        self._tasks[task.id] = task

    async def get(self, task_id: UUID) -> Task:
        return self._tasks[task_id]

    async def claim_queued(self, task_id: UUID) -> Task | None:
        task = self._tasks[task_id]
        if task.status is not TaskStatus.QUEUED:
            return None
        claimed = task.with_status(TaskStatus.RUNNING).model_copy(
            update={"attempt_count": task.attempt_count + 1}
        )
        self._tasks[task_id] = claimed
        return claimed

    async def update(self, task: Task) -> None:
        self._tasks[task.id] = task

    async def list_by_workflow(self, workflow_id: UUID) -> list[Task]:
        return [task for task in self._tasks.values() if task.workflow_id == workflow_id]


class InMemoryArtifactRepository:
    def __init__(self) -> None:
        self._artifacts_by_task: dict[UUID, list[Artifact]] = defaultdict(list)
        self._artifacts_by_workflow: dict[UUID, list[Artifact]] = defaultdict(list)

    async def add(self, artifact: Artifact) -> None:
        self._artifacts_by_workflow[artifact.workflow_id].append(artifact)
        if artifact.task_id is None:
            return
        self._artifacts_by_task[artifact.task_id].append(artifact)

    async def list_by_task(self, task_id: UUID) -> list[Artifact]:
        return list(self._artifacts_by_task[task_id])

    async def list_by_workflow(self, workflow_id: UUID) -> list[Artifact]:
        return list(self._artifacts_by_workflow[workflow_id])


class InMemoryTaskQueue:
    def __init__(self) -> None:
        self.enqueued_task_ids: list[UUID] = []

    async def enqueue_task(self, task_id: UUID) -> None:
        self.enqueued_task_ids.append(task_id)


class InMemoryTelemetry:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.counters: list[tuple[str, int, dict[str, Any]]] = []
        self.observations: list[tuple[str, float, dict[str, Any]]] = []

    async def event(self, name: str, attributes: dict[str, Any]) -> None:
        self.events.append((name, attributes))

    async def increment(
        self, name: str, attributes: dict[str, Any] | None = None, value: int = 1
    ) -> None:
        self.counters.append((name, value, attributes or {}))

    async def observe(
        self, name: str, value: float, attributes: dict[str, Any] | None = None
    ) -> None:
        self.observations.append((name, value, attributes or {}))


class InMemoryApprovalRepository:
    def __init__(self) -> None:
        self._gates: dict[UUID, ApprovalGate] = {}

    async def add(self, gate: ApprovalGate) -> None:
        self._gates[gate.id] = gate

    async def get(self, gate_id: UUID) -> ApprovalGate:
        return self._gates[gate_id]

    async def update(self, gate: ApprovalGate) -> None:
        self._gates[gate.id] = gate

    async def list_by_workflow(self, workflow_id: UUID) -> list[ApprovalGate]:
        return [gate for gate in self._gates.values() if gate.workflow_id == workflow_id]


class InMemoryExecutionEventRepository:
    def __init__(self) -> None:
        self._events: list[ExecutionEvent] = []

    async def add(self, event: ExecutionEvent) -> None:
        self._events.append(event)

    async def list_by_workflow(self, workflow_id: UUID) -> list[ExecutionEvent]:
        return [event for event in self._events if event.workflow_id == workflow_id]


class FakeGitService:
    def __init__(self) -> None:
        self.branches: list[tuple[str, str]] = []
        self.commits: list[tuple[str, list[str]]] = []
        self.pushes: list[tuple[str, str]] = []
        self.pull_requests: list[tuple[str, str, str, str]] = []
        self.rollback_count = 0
        self.fail_commit = False

    async def create_branch(self, branch_name: str, base_ref: str = "main") -> None:
        self.branches.append((branch_name, base_ref))

    async def diff(self) -> str:
        return "diff --git a/src/example.py b/src/example.py\n"

    async def commit(self, message: str, paths: list[str]) -> CommitResult:
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.commits.append((message, paths))
        return CommitResult(sha="0" * 40, message=message)

    async def push(self, branch_name: str, remote: str = "origin") -> None:
        self.pushes.append((branch_name, remote))

    async def rollback(self) -> None:
        self.rollback_count += 1

    async def open_pull_request(
        self, title: str, body: str, branch_name: str, base_ref: str = "main"
    ) -> PullRequestResult:
        self.pull_requests.append((title, body, branch_name, base_ref))
        return PullRequestResult(url=f"local://pull-request/{branch_name}", is_draft=True)


class FakeAgentClient:
    def __init__(self, *, reviewer_decision: ReviewDecision, include_tool_requests: bool = False) -> None:
        self._reviewer_decision = reviewer_decision
        self._include_tool_requests = include_tool_requests

    @classmethod
    def planner_with_two_tasks(cls) -> FakeAgentClient:
        return cls(reviewer_decision=ReviewDecision.APPROVE)

    @classmethod
    def approving_code_review(cls) -> FakeAgentClient:
        return cls(reviewer_decision=ReviewDecision.APPROVE)

    @classmethod
    def rejecting_code_review(cls) -> FakeAgentClient:
        return cls(reviewer_decision=ReviewDecision.REQUEST_FIXES)

    @classmethod
    def approving_code_review_with_tool_requests(cls) -> FakeAgentClient:
        return cls(reviewer_decision=ReviewDecision.APPROVE, include_tool_requests=True)

    async def plan(self, request: AgentInput) -> PlannerOutput:
        return PlannerOutput(
            summary=f"Plan for {request.objective}",
            tasks=[
                PlannedTask(
                    kind=TaskKind.CODING,
                    title="Implement requested change",
                    description=request.objective,
                ),
                PlannedTask(
                    kind=TaskKind.TESTING,
                    title="Validate requested change",
                    description=f"Validate: {request.objective}",
                    depends_on=[0],
                ),
            ],
        )

    async def code(self, request: AgentInput) -> CoderOutput:
        return CoderOutput(
            summary=f"Implemented {request.objective}",
            changed_files=["src/example.py"],
            artifacts=[
                {
                    "kind": "diff",
                    "filename": "change.diff",
                    "content": "diff --git a/src/example.py b/src/example.py\n",
                }
            ],
            tool_requests=(
                [{"tool_name": "pytest", "args": ["-q"]}] if self._include_tool_requests else []
            ),
        )

    async def test(self, request: AgentInput) -> TesterOutput:
        return TesterOutput(
            passed=True,
            command="pytest",
            summary="Tests passed in fake sandbox.",
            artifacts=[{"kind": "test_report", "filename": "pytest.txt", "content": "1 passed"}],
            tool_requests=(
                [{"tool_name": "pytest", "args": ["-q"]}] if self._include_tool_requests else []
            ),
        )

    async def review(self, request: AgentInput) -> ReviewerOutput:
        if self._reviewer_decision is ReviewDecision.APPROVE:
            return ReviewerOutput(decision=ReviewDecision.APPROVE)
        return ReviewerOutput(
            decision=ReviewDecision.REQUEST_FIXES,
            findings=[
                ReviewerFinding(
                    severity=Severity.HIGH,
                    category="architecture",
                    message="Implementation does not satisfy reviewer policy.",
                )
            ],
            required_fixes=["Address reviewer policy findings."],
        )
