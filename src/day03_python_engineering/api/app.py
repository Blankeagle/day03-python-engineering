from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from fastapi import FastAPI
from day03_python_engineering.api.dependencies import (
    close_dependencies,
    create_agent,
    get_session_manager,
)
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from day03_python_engineering.api.dependencies import close_dependencies
from day03_python_engineering.api.routes import router
from day03_python_engineering.exceptions import (
    OllamaServiceError,
    OllamaTimeoutError,
)
from day03_python_engineering.logging_config import setup_logging


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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