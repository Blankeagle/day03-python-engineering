from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class VectorDocument:
    id: str
    text: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    document: VectorDocument
    score: float


class VectorStore(Protocol):
    def add(
        self,
        document_id: str,
        text: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def search(
        self,
        query_vector: list[float],
        top_k: int = 3,
    ) -> list[SearchResult]:
        ...

    def delete_by_source(
        self,
        source: str,
    ) -> None:
        ...

