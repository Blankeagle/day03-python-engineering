from pydantic import BaseModel, Field

from day03_python_engineering.rag.service import RAGService


class RAGQueryInput(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


async def search_knowledge_base(
    question: str,
    rag_service: RAGService,
) -> str:
    result = await rag_service.answer(
        question=question,
        top_k=3,
    )

    return result.answer