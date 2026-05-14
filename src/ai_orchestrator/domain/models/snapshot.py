from __future__ import annotations

from pydantic import BaseModel

from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow


class WorkflowSnapshot(BaseModel):
    workflow: Workflow
    tasks: list[Task]
