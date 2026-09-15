from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.rag.retriever import Retriever
from day03_python_engineering.rag.result import (
    RAGResponse,
    RAGSource,
)

class RAGService:
    def __init__(
        self,
        retriever: Retriever,
        llm_client: OllamaClient,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
    async def answer(
        self,
        question: str,
        top_k: int = 3,
        min_score: float = 0.5,
    ) -> RAGResponse:
        results = await self.retriever.retrieve(
            question=question,
            top_k=top_k,
            min_score=min_score,
        )

        if not results:
            return RAGResponse(
                answer="I don't know based on the available documents.",
                sources=[],
            )

        context = "\n\n".join(
            result.document.text
            for result in results
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Answer the question using only the provided context. "
                    "If the answer is not in the context, say you don't know."
                ),
            },
            {
                "role": "user",
                "content": f"""
    Context:
    {context}

    Question:
    {question}
    """,
            },
        ]

        response = await self.llm_client.chat(
            messages=messages
        )

        answer = response["message"]["content"]

        sources = [
            result.document.metadata
            for result in results
        ]
        source_text = "\n".join(
            f"- {item.get('source')} (chunk {item.get('chunk_id')})"
            for item in sources
        )

        return RAGResponse(
            answer=answer,
            sources=[
                RAGSource(source=item.get('source'), chunk_id=item.get('chunk_id'))
                for item in sources
            ]
        )
