"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-14
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    migration = Path(__file__).resolve().parents[2] / "migrations" / "0001_initial.sql"
    op.execute(migration.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS approval_gates")
    op.execute("DROP TABLE IF EXISTS execution_history")
    op.execute("DROP TABLE IF EXISTS memory_records")
    op.execute("DROP TABLE IF EXISTS review_results")
    op.execute("DROP TABLE IF EXISTS agent_runs")
    op.execute("DROP TABLE IF EXISTS artifacts")
    op.execute("DROP TABLE IF EXISTS task_dependencies")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS workflows")
