from day03_python_engineering.rag.embedding_client import EmbeddingClient
from day03_python_engineering.rag.store import SearchResult, VectorStore


class Retriever:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        store: VectorStore,
    ):
        self.embedding_client = embedding_client
        self.store = store

    async def retrieve(
        self,
        question: str,
        top_k: int = 3,
        min_score: float = 0.5,
    ) -> list[SearchResult]:
        query_vector = await self.embedding_client.embed(
            question
        )

        results = self.store.search(
            query_vector=query_vector,
            top_k=top_k,
        )

      

        return [result for result in results if result.score >= min_score]
