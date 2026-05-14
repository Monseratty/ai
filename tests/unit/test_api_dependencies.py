from __future__ import annotations

import inspect
from pathlib import Path

from ai_orchestrator.api.deps import get_composition_root, get_orchestrator
from ai_orchestrator.config.settings import Settings
from ai_orchestrator.infrastructure.composition import CompositionRoot


def test_get_composition_root_returns_cached_root() -> None:
    get_composition_root.cache_clear()

    first = get_composition_root()
    second = get_composition_root()

    assert first is second
    assert isinstance(first, CompositionRoot)


def test_get_orchestrator_is_async_generator_dependency() -> None:
    assert inspect.isasyncgenfunction(get_orchestrator)


def test_composition_root_can_be_built_with_explicit_artifact_root(tmp_path: Path) -> None:
    root = CompositionRoot(settings=Settings(artifact_root=tmp_path))

    assert root.settings.artifact_root == tmp_path
