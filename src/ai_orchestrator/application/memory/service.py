from __future__ import annotations

from pydantic import BaseModel, Field

from ai_orchestrator.interfaces.vector_memory import VectorMemory


class ScopedMemory(BaseModel):
    short_term: list[str] = Field(default_factory=list)
    long_term: list[str] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)


class MemoryService:
    def __init__(self, vector_memory: VectorMemory | None = None) -> None:
        self._vector_memory = vector_memory

    async def load_scoped_memory(self, workflow_id: str, query: str) -> ScopedMemory:
        if self._vector_memory is None:
            return ScopedMemory()
        records = await self._vector_memory.search(namespace=workflow_id, query=query, limit=5)
        return ScopedMemory(long_term=[record.content for record in records])

