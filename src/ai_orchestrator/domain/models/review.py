from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from ai_orchestrator.domain.enums import ReviewDecision
from ai_orchestrator.domain.models.common import new_id, utc_now
from datetime import datetime


class TaskExecutionResult(BaseModel):
    task_id: UUID
    workflow_id: UUID
    review_decision: ReviewDecision | None = None
    created_feedback_task_id: UUID | None = None
    artifacts_created: int = 0
    summary: str


class ReviewResult(BaseModel):
    id: UUID = Field(default_factory=new_id)
    workflow_id: UUID
    task_id: UUID
    decision: ReviewDecision
    findings: list[dict] = Field(default_factory=list)
    required_fixes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
