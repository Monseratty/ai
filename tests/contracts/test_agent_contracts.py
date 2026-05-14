from __future__ import annotations

from pydantic import ValidationError
import pytest

from ai_orchestrator.application.agents.schemas import (
    CoderOutput,
    PlannedTask,
    PlannerOutput,
    ReviewerFinding,
    ReviewerOutput,
    TesterOutput,
)
from ai_orchestrator.domain.enums import ReviewDecision, Severity, TaskKind


def test_planner_output_requires_structured_task_graph() -> None:
    output = PlannerOutput(
        summary="Implement API and tests",
        tasks=[
            PlannedTask(
                kind=TaskKind.CODING,
                title="Add API endpoint",
                description="Create a typed FastAPI endpoint.",
                depends_on=[],
            ),
            PlannedTask(
                kind=TaskKind.TESTING,
                title="Validate API endpoint",
                description="Run endpoint tests.",
                depends_on=[0],
            ),
        ],
    )

    assert output.tasks[1].depends_on == [0]


def test_planner_rejects_dependency_indexes_that_point_past_task_list() -> None:
    with pytest.raises(ValidationError):
        PlannerOutput(
            summary="Invalid graph",
            tasks=[
                PlannedTask(
                    kind=TaskKind.CODING,
                    title="Only task",
                    description="No dependency target exists.",
                    depends_on=[2],
                )
            ],
        )


def test_reviewer_output_is_structured_and_actionable() -> None:
    output = ReviewerOutput(
        decision=ReviewDecision.REQUEST_FIXES,
        findings=[
            ReviewerFinding(
                severity=Severity.HIGH,
                category="security",
                message="Sandbox mounts host secrets.",
                file_path="src/sandbox.py",
                line=42,
            )
        ],
        required_fixes=["Remove secret mount from sandbox policy."],
    )

    assert output.required_fixes == ["Remove secret mount from sandbox policy."]


def test_coder_and_tester_outputs_are_artifact_oriented() -> None:
    coder = CoderOutput(
        summary="Added repository protocols.",
        changed_files=["src/ai_orchestrator/interfaces/repositories.py"],
        artifacts=[{"kind": "diff", "path": "artifacts/change.diff"}],
        tool_requests=[{"tool_name": "pytest", "args": ["tests/orchestration", "-q"]}],
    )
    tester = TesterOutput(
        passed=True,
        command="pytest tests/orchestration -q",
        summary="3 passed",
        artifacts=[{"kind": "test_report", "path": "artifacts/pytest.txt"}],
        tool_requests=[{"tool_name": "pytest", "args": ["tests/orchestration", "-q"]}],
    )

    assert coder.changed_files == ["src/ai_orchestrator/interfaces/repositories.py"]
    assert tester.passed is True
    assert coder.tool_requests[0]["tool_name"] == "pytest"
