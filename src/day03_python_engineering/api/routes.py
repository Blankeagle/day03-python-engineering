from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from fastapi.responses import StreamingResponse

from day03_python_engineering.agent.stream_event import (
    serialize_stream_event,
)
from day03_python_engineering.api.dependencies import (
    create_agent,
    get_checkpointer,
    get_session_manager,
)
from day03_python_engineering.session.manager import SessionManager
from day03_python_engineering.api.dependencies import (
    get_rag_service ,
    get_memory_service
    )
from day03_python_engineering.rag.result import RAGResponse
from day03_python_engineering.rag.service import RAGService
from src.day03_python_engineering.memory.service import MemoryService
from day03_python_engineering.agent.result import AgentRunResult
from day03_python_engineering.agent.stream_event import (
    AgentStreamEvent,
    serialize_stream_event,
)

router = APIRouter()


class ChatData(BaseModel):
    # Describe the current workflow state
    status: str

    # Store the final answer after workflow completion
    answer: str | None = None

    # Identify the workflow execution for later resume
    thread_id: str | None = None

    # Store interrupt information when the workflow is paused
    interrupt: Any | None = None


class ChatResponse(BaseModel):
    success: bool
    data: ChatData
   

class RAGQueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


class ChatRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=100,
    )

    session_id: str = Field(
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        min_length=1,
        max_length=2000,
    )

class ResumeRequest(BaseModel):
    # Identify the conversation session
    session_id: str = Field(
        min_length=1,
        max_length=100,
    )

    # Identify the interrupted workflow execution
    thread_id: str = Field(
        min_length=1,
        max_length=200,
    )

    # Provide the user's approval decision
    decision: bool

from typing import Any


class ChatData(BaseModel):
    # Describe the current workflow state
    status: str

    # Store the final answer after workflow completion
    answer: str | None = None

    # Identify the workflow execution for later resume
    thread_id: str | None = None

    # Store interrupt information when the workflow is paused
    interrupt: Any | None = None


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
    memory_service: MemoryService = Depends(get_memory_service),
    checkpointer=Depends(get_checkpointer),

):
    async with session_manager.lock(request.session_id):
        agent = session_manager.get(request.session_id)

        if agent is None:
            messages = await session_manager.load_messages(request.session_id)
            agent = create_agent(checkpointer=checkpointer,)
            if messages is not None:
                agent.messages = messages

        # set long term memory for the agent
        memory = await memory_service.get_memory(request.user_id)
        memory_prompt = memory.to_prompt()
        agent.set_user_memory(memory_prompt)

        result = await agent.run(request.message,request.session_id)

        # save the session history after processing the message
        await session_manager.set(request.session_id, agent)

      

        # update long term memory based on the user input
        await memory_service.process_message(
            user_id=request.user_id,
            message=request.message,
        )

    return build_chat_response(result)

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    memory_service: MemoryService = Depends(get_memory_service),
    checkpointer=Depends(get_checkpointer),
):
    # Stream public agent events to the client
    async def event_generator():
        async with session_manager.lock(request.session_id):
            agent = session_manager.get(request.session_id)

            if agent is None:
                messages = await session_manager.load_messages(
                    request.session_id
                )

                agent = create_agent(
                    checkpointer=checkpointer,
                )

                if messages is not None:
                    agent.messages = messages

            # Load long-term memory for the current user
            memory = await memory_service.get_memory(request.user_id)
            memory_prompt = memory.to_prompt()
            agent.set_user_memory(memory_prompt)

            # Track whether the workflow completed successfully
            completed = False

        # Stream agent workflow events
        try:
            # Stream agent workflow events
            async for event in agent.stream(
                user_message=request.message,
                session_id=request.session_id,
            ):
                if event.event == "completed":
                    completed = True

                yield serialize_stream_event(event)

        except Exception:
            # Return a safe public error without exposing internal details
            error_event = AgentStreamEvent(
                event="error",
                data={
                    "message": "Agent workflow failed.",
                },
            )
            yield serialize_stream_event(error_event)
            return

            # Persist conversation data only after successful completion
        if completed:
            await session_manager.set(
                request.session_id,
                agent,
            )

            await memory_service.process_message(
                user_id=request.user_id,
                message=request.message,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
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


@router.post("/chat/resume", response_model=ChatResponse)
async def resume_chat(
    request: ResumeRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    checkpointer=Depends(get_checkpointer),
):
    # Protect the same session from concurrent modifications
    async with session_manager.lock(request.session_id):
        agent = session_manager.get(request.session_id)

        # Recreate the agent when the in-memory cache was lost after restart
        if agent is None:
            agent = create_agent(
                checkpointer=checkpointer,
            )

            # Restore the conversation history from Redis
        messages = await session_manager.load_messages(
            request.session_id,
        )

        if messages is not None:
            agent.messages = messages

        # Resume the interrupted workflow using the original thread ID
        result = await agent.resume(
            thread_id=request.thread_id,
            decision=request.decision,
        )
        # Save the updated conversation after resuming the workflow
        await session_manager.set(
            request.session_id,
            agent,
        )
    return build_chat_response(result)





def build_chat_response(result: AgentRunResult) -> ChatResponse:
    # Build a response for an interrupted workflow
    if result.status == "interrupted":
        return ChatResponse(
            success=True,
            data=ChatData(
                status=result.status,
                thread_id=result.thread_id,
                interrupt=result.interrupt,
            ),
        )

    # Build a response for a completed workflow
    return ChatResponse(
        success=True,
        data=ChatData(
            status=result.status,
            answer=result.answer,
            thread_id=result.thread_id,
        ),
    )

