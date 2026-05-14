from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIO_", env_file=".env", extra="ignore")

    app_name: str = "AI Software Engineering Orchestrator"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://orchestrator:orchestrator@localhost:5432/orchestrator"
    redis_url: str = "redis://localhost:6379/0"
    sandbox_image: str = "python:3.12-slim"
    sandbox_timeout_seconds: int = 300
    sandbox_memory: str = "1g"
    sandbox_cpus: float = 1.0
    sandbox_workspace_root: Path = Path(".sandboxes")
    sandbox_allowed_commands: set[str] = Field(default_factory=lambda: {"python", "pytest", "ruff"})
    openai_model: str = "gpt-5.2"
    planner_model: str | None = None
    coder_model: str | None = None
    tester_model: str | None = None
    reviewer_model: str | None = None
    agent_backend: str = "fake"
    artifact_root: Path = Path(".artifacts")
    repo_path: Path = Path(".")
    pull_request_provider: str = "local"
    github_repository: str | None = None
    github_token: str | None = None
    api_token: str | None = None
    api_rate_limit_per_minute: int = Field(default=60, ge=1)
    telemetry_backend: str = "logging"


def get_settings() -> Settings:
    return Settings()
