from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from day03_python_engineering.api.dependencies import (
    create_agent,
    get_session_manager,
)
from day03_python_engineering.session.manager import SessionManager
from day03_python_engineering.api.dependencies import get_rag_service
from day03_python_engineering.rag.result import RAGResponse
from day03_python_engineering.rag.service import RAGService
router = APIRouter()


class RAGQueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100, description="会话 ID")
    message: str = Field(min_length=1, max_length=2000, description="用户输入内容")


class ChatData(BaseModel):
    answer: str


class ChatResponse(BaseModel):
    success: bool
    data: ChatData


@router.get("/")
def root():
    return {"message": "Day4 Agent API is running"}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager),
):
    async with session_manager.lock(request.session_id):
        agent = session_manager.get(request.session_id)

        if agent is None:
            messages = await session_manager.load_messages(request.session_id)
            agent = create_agent()
            if messages is not None:
                agent.messages = messages

        answer = await agent.run(request.message)
        await session_manager.set(request.session_id, agent)

    return ChatResponse(
        success=True,
        data=ChatData(answer=answer),
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
):
    async with session_manager.lock(session_id):
        if not await session_manager.exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        await session_manager.delete(session_id)
    return {"message": "session deleted"}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post(
    "/rag/query",
    response_model=RAGResponse,
)
async def rag_query(
    request: RAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGResponse:
    return await rag_service.answer(
        question=request.question,
        top_k=3,
    )
