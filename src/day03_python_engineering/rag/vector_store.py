from typing import Any
from day03_python_engineering.rag.similarity import cosine_similarity
from day03_python_engineering.rag.store import SearchResult, VectorDocument

class InMemoryVectorStore:
    def __init__(self):
        self._documents: list[VectorDocument] = []

    def add(
    self,
    document_id: str,
    text: str,
    vector: list[float],
    metadata: dict[str, Any] | None = None,
) -> None:
        self._documents.append(
            VectorDocument(
                id=document_id,
                text=text,
                vector=vector,
                metadata=metadata or {},
            )
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 3,
    ) -> list[SearchResult]:
        results = []

        for document in self._documents:
            score = cosine_similarity(
                query_vector,
                document.vector,
            )

            results.append(
                SearchResult(
                    document=document,
                    score=score,
                )
            )

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results[:top_k]

    def delete_by_source(
        self,
        source: str,
    ) -> None:
        self._documents = [
            document
            for document in self._documents
            if document.metadata.get("source") != source
        ]
