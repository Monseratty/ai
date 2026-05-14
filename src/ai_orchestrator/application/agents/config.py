from __future__ import annotations

from pydantic import BaseModel


class AgentModelConfig(BaseModel):
    planner_model: str
    coder_model: str
    tester_model: str
    reviewer_model: str

    @classmethod
    def single_model(cls, model: str) -> AgentModelConfig:
        return cls(
            planner_model=model,
            coder_model=model,
            tester_model=model,
            reviewer_model=model,
        )
