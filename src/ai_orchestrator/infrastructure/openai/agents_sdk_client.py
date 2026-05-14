from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ai_orchestrator.application.agents.config import AgentModelConfig
from ai_orchestrator.application.agents.schemas import (
    AgentInput,
    CoderOutput,
    PlannerOutput,
    ReviewerOutput,
    TesterOutput,
)
from ai_orchestrator.application.agents.prompts import (
    CODER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    TESTER_SYSTEM_PROMPT,
)

TOutput = TypeVar("TOutput", bound=BaseModel)

AgentRunner = Callable[..., Awaitable[object]]


class AgentOutputValidationError(RuntimeError):
    """Raised when an agent cannot produce schema-valid structured output."""


class OpenAIAgentsSDKClient:
    """Adapter boundary for OpenAI Agents SDK.

    The implementation is intentionally isolated so orchestration tests do not depend on
    network access or nondeterministic model behavior.
    """

    def __init__(
        self,
        model: str | None = None,
        model_config: AgentModelConfig | None = None,
        *,
        runner: AgentRunner | None = None,
        max_output_retries: int = 2,
    ) -> None:
        self._model_config = model_config or AgentModelConfig.single_model(model or "gpt-5.2")
        self._runner = runner
        self._max_output_retries = max_output_retries

    async def plan(self, request: AgentInput) -> PlannerOutput:
        return await self._run_agent(
            name="PlannerAgent",
            instructions=PLANNER_SYSTEM_PROMPT,
            request=request,
            output_type=PlannerOutput,
            model=self._model_config.planner_model,
        )

    async def code(self, request: AgentInput) -> CoderOutput:
        return await self._run_agent(
            name="CoderAgent",
            instructions=CODER_SYSTEM_PROMPT,
            request=request,
            output_type=CoderOutput,
            model=self._model_config.coder_model,
        )

    async def test(self, request: AgentInput) -> TesterOutput:
        return await self._run_agent(
            name="TesterAgent",
            instructions=TESTER_SYSTEM_PROMPT,
            request=request,
            output_type=TesterOutput,
            model=self._model_config.tester_model,
        )

    async def review(self, request: AgentInput) -> ReviewerOutput:
        return await self._run_agent(
            name="ReviewerAgent",
            instructions=REVIEWER_SYSTEM_PROMPT,
            request=request,
            output_type=ReviewerOutput,
            model=self._model_config.reviewer_model,
        )

    def render_input(self, request: AgentInput) -> str:
        return json.dumps(request.model_dump(mode="json"), ensure_ascii=True, indent=2)

    def coerce_output(self, final_output: object, output_type: type[TOutput]) -> TOutput:
        if isinstance(final_output, output_type):
            return final_output
        if isinstance(final_output, str):
            return output_type.model_validate_json(final_output)
        return output_type.model_validate(final_output)

    async def _run_agent(
        self,
        *,
        name: str,
        instructions: str,
        request: AgentInput,
        output_type: type[TOutput],
        model: str,
    ) -> TOutput:
        rendered_input = self.render_input(request)
        last_error: Exception | None = None
        attempts = max(1, self._max_output_retries + 1)
        for _ in range(attempts):
            try:
                final_output = await self._call_runner(
                    agent_name=name,
                    instructions=instructions,
                    model=model,
                    output_type=output_type,
                    rendered_input=rendered_input,
                )
                return self.coerce_output(final_output, output_type)
            except ValidationError as exc:
                last_error = exc
                continue
        raise AgentOutputValidationError(
            f"{name} failed to produce valid {output_type.__name__} after {attempts} attempts."
        ) from last_error

    async def _call_runner(
        self,
        *,
        agent_name: str,
        instructions: str,
        model: str,
        output_type: type[TOutput],
        rendered_input: str,
    ) -> object:
        if self._runner is not None:
            return await self._runner(
                agent_name=agent_name,
                instructions=instructions,
                model=model,
                output_type=output_type,
                rendered_input=rendered_input,
            )

        try:
            from agents import Agent, Runner
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI Agents SDK is not installed. Install the 'openai-agents' package."
            ) from exc

        agent = Agent(
            name=agent_name,
            instructions=instructions,
            model=model,
            output_type=output_type,
        )
        result = await Runner.run(agent, rendered_input)
        return result.final_output
