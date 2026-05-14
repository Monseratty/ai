from __future__ import annotations

from ai_orchestrator.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork


def test_sqlalchemy_unit_of_work_exposes_required_repositories() -> None:
    unit = SqlAlchemyUnitOfWork(session=object())  # type: ignore[arg-type]

    assert unit.workflows is not None
    assert unit.tasks is not None
    assert unit.artifacts is not None
    assert unit.approvals is not None
    assert unit.execution_events is not None
