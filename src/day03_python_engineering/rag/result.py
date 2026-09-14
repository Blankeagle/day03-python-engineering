from pydantic import BaseModel


class RAGSource(BaseModel):
    source: str
    chunk_id: int


class RAGResponse(BaseModel):
    answer: str
    sources: list[RAGSource]