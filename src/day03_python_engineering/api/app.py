from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from day03_python_engineering.api.dependencies import (
    create_agent,
    get_session_manager,
)
from day03_python_engineering.exceptions import (
    OllamaServiceError,
    OllamaTimeoutError,
)
from day03_python_engineering.session.manager import SessionManager
from day03_python_engineering.agent.agent import Agent
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

import logging

from day03_python_engineering.logging_config import setup_logging
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

class ErrorInfo(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorInfo




class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100,
        description="会话 ID",
    ) 

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="用户输入内容",
    )

class ChatData(BaseModel):
    answer: str

class ChatResponse(BaseModel):
    success: bool
    data: ChatData

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Day4 AI Agent API",
        version="0.1.0",
    )

    @app.exception_handler(OllamaTimeoutError)
    async def ollama_timeout_handler(
        request: Request,
        exc: OllamaTimeoutError,
    ):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "OLLAMA_TIMEOUT",
                    "message": "Ollama request timed out",
                },
            },
        )

    @app.exception_handler(OllamaServiceError)
    async def ollama_service_handler(
        request: Request,
        exc: OllamaServiceError,
    ):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "OLLAMA_UNAVAILABLE",
                    "message": "Ollama service is unavailable",
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                },
            },
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception(
            "Unhandled exception"
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                },
            },
        )
    
    # ③ 路由
    @app.get("/")
    def root():
        return {
            "message": "Day4 Agent API is running"
        }

    @app.post(
        "/chat",
        response_model=ChatResponse,
    )
    def chat(
        request: ChatRequest,
        session_manager: SessionManager = Depends(
            get_session_manager
        ),
    ):
        agent = session_manager.get(request.session_id)

        if agent is None:
            agent = create_agent()

            session_manager.set(
                request.session_id,
                agent,
            )

        answer = agent.run(request.message)

        return ChatResponse(
            success=True,
            data=ChatData(answer=answer)
        )

    @app.delete("/sessions/{session_id}")
    def delete_session(
        session_id: str,
        session_manager: SessionManager = Depends(
            get_session_manager
        ),
    ):
        if not session_manager.exists(session_id):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

        session_manager.delete(session_id)

        return {
            "message": "session deleted"
        }

    @app.get("/health")
    def health():
        return {
            "status": "ok"
        }

    # ④ 返回 FastAPI 对象
    return app

   


# ⑤ 真正创建 app
app = create_app()