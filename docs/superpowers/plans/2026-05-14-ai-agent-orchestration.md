# AI Agent Orchestration Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a typed, modular, testable AI software engineering orchestration framework skeleton with mandatory planner, coder, tester, reviewer, memory, task graph, git, sandbox, queue, telemetry, and documentation boundaries.

**Architecture:** Clean architecture with domain models and protocols at the center, application orchestration services around them, and FastAPI/Postgres/Celery/Docker/Git/OpenAI adapters at the edge. Agents are stateless and communicate only through structured Pydantic schemas.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy async, Postgres, Redis, Celery, OpenAI Agents SDK boundary, Docker sandbox boundary, GitPython boundary, pytest, asyncio.

---

## File Structure

- `pyproject.toml`: package metadata, dependencies, pytest config.
- `src/ai_orchestrator/domain/`: typed domain entities, enums, and events.
- `src/ai_orchestrator/interfaces/`: protocols for agents, repositories, queue, sandbox, git, telemetry, vector memory.
- `src/ai_orchestrator/application/`: orchestration service, state machine, reviewer loop, memory service, policies.
- `src/ai_orchestrator/infrastructure/`: adapter skeletons for DB, OpenAI, sandbox, git, queue, telemetry.
- `src/ai_orchestrator/api/`: FastAPI app and workflow endpoints.
- `tests/contracts/`: agent schema and stateless contract tests.
- `tests/orchestration/`: end-to-end workflow orchestration tests with fakes.
- `docs/`: architecture, setup, deployment, adding agents, security.

## Tasks

- [ ] Create failing orchestration and contract tests for planner decomposition, mandatory reviewer loop, and bounded retry behavior.
- [ ] Add domain enums and Pydantic models for workflows, tasks, artifacts, memory, agent runs, reviews, git changes, and events.
- [ ] Add interface protocols for agent client, repositories, task queue, sandbox executor, git service, telemetry, and vector memory.
- [ ] Add application orchestration service with explicit lifecycle state transitions and race-condition checks.
- [ ] Add fake in-memory repositories and fake agent client for deterministic tests.
- [ ] Add infrastructure adapter skeletons for FastAPI, SQLAlchemy/Postgres, Celery/Redis, Docker, GitPython, OpenAI Agents SDK, and telemetry.
- [ ] Add documentation covering architecture, local setup, deployment, security, and adding new agents.
- [ ] Run tests and static checks available in the local environment.
