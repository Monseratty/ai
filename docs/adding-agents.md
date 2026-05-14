# Adding New Agents

## Steps

1. Define the agent responsibility in one sentence.
2. Add input/output schemas in `src/ai_orchestrator/application/agents/schemas.py`.
3. Add a narrow system prompt in `src/ai_orchestrator/application/agents/prompts.py`.
4. Extend the `AgentClient` protocol only if the new responsibility cannot fit an existing method.
5. Add fake deterministic behavior for tests.
6. Add contract tests for schema validation.
7. Add orchestration tests for lifecycle transitions.

## Rules

- The agent must be stateless.
- The agent must return structured JSON.
- The agent must not access repositories, queues, or filesystem directly.
- The orchestration layer decides whether output mutates canonical state.
- Sensitive tools require policy checks and approval gates.

