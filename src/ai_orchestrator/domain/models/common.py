from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


def new_id() -> UUID:
    return uuid4()


def utc_now() -> datetime:
    return datetime.now(UTC)

