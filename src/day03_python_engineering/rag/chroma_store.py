import chromadb

from typing import Any

from day03_python_engineering.rag.vector_store import VectorDocument
from day03_python_engineering.rag.store import SearchResult
class ChromaVectorStore:
    def __init__(
        self,
        path: str = "data/chroma_db",
        collection_name: str = "documents",
    ):
        self.client = chromadb.PersistentClient(
            path=path,
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine",
                },
            )
        )

    def add(
        self,
        document_id: str,
        text: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.collection.upsert(
            ids=[document_id],
            documents=[text],
            embeddings=[vector],
            metadatas=[metadata or {}],
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 3,
    ) -> list[SearchResult]:
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        output = []

        for document_id, text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            document = VectorDocument(
                id=document_id,
                text=text,
                vector=[],
                metadata=metadata or {},
            )

            score = 1 / (1 + distance)

            output.append(
                SearchResult(
                    document=document,
                    score=score,
                )
            )

        return output

    def delete_by_source(self, source: str) -> None:
        self.collection.delete(
            where={
                "source": source,
            }
        )
