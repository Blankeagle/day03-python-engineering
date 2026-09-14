from enum import Enum
from typing import Any

from pydantic import BaseModel


class ToolErrorCode(str, Enum):
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_DISABLED = "TOOL_DISABLED"
    TOOL_GROUP_FORBIDDEN = "TOOL_GROUP_FORBIDDEN"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_HTTP_ERROR = "TOOL_HTTP_ERROR"
    TOOL_NETWORK_ERROR = "TOOL_NETWORK_ERROR"


class ToolResult(BaseModel):
    success: bool
    data: Any | None = None
    error: ToolErrorCode | None = None
    message: str | None = None
    retryable: bool = False