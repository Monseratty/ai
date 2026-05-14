from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class VectorMemoryRecord(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class VectorMemory(Protocol):
    async def upsert(self, namespace: str, record_id: str, content: str, metadata: dict) -> None: ...

    async def search(self, namespace: str, query: str, limit: int = 5) -> list[VectorMemoryRecord]: ...

