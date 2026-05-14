from __future__ import annotations

from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ai_orchestrator.domain.enums import ReviewDecision, Severity, TaskKind


class AgentInput(BaseModel):
    workflow_id: UUID
    task_id: UUID | None = None
    objective: str
    memory: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


class PlannedTask(BaseModel):
    kind: TaskKind
    title: str
    description: str
    depends_on: list[int] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    summary: str
    tasks: list[PlannedTask]

    @model_validator(mode="after")
    def validate_dependency_indexes(self) -> PlannerOutput:
        task_count = len(self.tasks)
        for index, task in enumerate(self.tasks):
            for dependency_index in task.depends_on:
                if dependency_index < 0 or dependency_index >= task_count:
                    raise ValueError(
                        f"Task {index} depends on missing task index {dependency_index}."
                    )
                if dependency_index == index:
                    raise ValueError(f"Task {index} cannot depend on itself.")
        return self


class CoderOutput(BaseModel):
    summary: str
    changed_files: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    tool_requests: list[dict[str, Any]] = Field(default_factory=list)


class TesterOutput(BaseModel):
    __test__: ClassVar[bool] = False

    passed: bool
    command: str
    summary: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    tool_requests: list[dict[str, Any]] = Field(default_factory=list)


class ReviewerFinding(BaseModel):
    severity: Severity
    category: str
    message: str
    file_path: str | None = None
    line: int | None = None


class ReviewerOutput(BaseModel):
    decision: ReviewDecision
    findings: list[ReviewerFinding] = Field(default_factory=list)
    required_fixes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_requested_fixes_are_actionable(self) -> ReviewerOutput:
        if self.decision is ReviewDecision.REQUEST_FIXES and not self.required_fixes:
            raise ValueError("Reviewer must provide required fixes when requesting fixes.")
        if self.decision is ReviewDecision.REJECT and not self.findings:
            raise ValueError("Reviewer must provide findings when rejecting work.")
        return self
