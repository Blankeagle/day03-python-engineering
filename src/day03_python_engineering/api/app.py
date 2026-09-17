import logging
import uuid
from contextlib import asynccontextmanager

from pydantic.v1 import Field
from pydantic.v1 import BaseModel
from fastapi import Depends

from day03_python_engineering.rag.result import RAGResponse
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from day03_python_engineering.api.dependencies import close_dependencies, initialize_rag
from day03_python_engineering.api.routes import router
from day03_python_engineering.exceptions import (
    OllamaServiceError,
    OllamaTimeoutError,
)
from day03_python_engineering.logging_config import setup_logging
from day03_python_engineering.request_context import request_id_var
from day03_python_engineering.api.dependencies import get_rag_service
from day03_python_engineering.rag.service import RAGService

from day03_python_engineering.exceptions import AgentWorkflowError

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_rag()


    yield
    await close_dependencies()


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message},
        },
    )


async def ollama_timeout_handler(request: Request, exc: OllamaTimeoutError):
    return _error_response(503, "OLLAMA_TIMEOUT", "Ollama request timed out")


async def ollama_service_handler(request: Request, exc: OllamaServiceError):
    return _error_response(
        503,
        "OLLAMA_UNAVAILABLE",
        "Ollama service is unavailable",
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return _error_response(422, "VALIDATION_ERROR", "Invalid request data")


async def unknown_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return _error_response(500, "INTERNAL_ERROR", "Internal server error")



def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Day4 AI Agent API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    app.add_exception_handler(OllamaTimeoutError, ollama_timeout_handler)
    app.add_exception_handler(OllamaServiceError, ollama_service_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unknown_exception_handler)
    return app

app = create_app()


@app.middleware("http")
async def add_request_id(
    request: Request,
    call_next,
):
    request_id = uuid.uuid4().hex
    token = request_id_var.set(request_id)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_var.reset(token)



@app.exception_handler(AgentWorkflowError)
async def agent_workflow_error_handler(
    request: Request,
    exc: AgentWorkflowError,
):
    # Convert the agent workflow error into a stable API response
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "AGENT_WORKFLOW_ERROR",
                "message": str(exc),
            },
        },
    )
