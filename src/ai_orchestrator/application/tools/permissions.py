from __future__ import annotations

from dataclasses import dataclass, field

from ai_orchestrator.application.orchestrator.policies import ToolPermissionError
from ai_orchestrator.domain.enums import AgentType, TaskKind


ToolGrantKey = tuple[AgentType, TaskKind]


@dataclass(frozen=True)
class ToolPermissionPolicy:
    grants: dict[ToolGrantKey, set[str]] = field(default_factory=dict)

    def validate(
        self,
        *,
        tool_name: str,
        agent_type: AgentType | None,
        task_kind: TaskKind | None,
    ) -> None:
        if agent_type is None or task_kind is None:
            return

        allowed = self.grants.get((agent_type, task_kind))
        if allowed is None:
            raise ToolPermissionError(
                f"Agent {agent_type.value!r} has no tool grants for task kind {task_kind.value!r}."
            )
        if tool_name not in allowed:
            raise ToolPermissionError(
                f"Tool {tool_name!r} is not allowed for agent {agent_type.value!r} "
                f"on task kind {task_kind.value!r}."
            )
