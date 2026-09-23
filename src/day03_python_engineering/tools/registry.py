import asyncio
import inspect
import json
import logging
import random
import time

import httpx

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from day03_python_engineering.request_context import request_id_var
from day03_python_engineering.tools.definition import ToolDefinition

from pydantic import BaseModel ,ValidationError
from day03_python_engineering.tools.result import ToolErrorCode, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
    ):
        self._tools: dict[str, ToolDefinition] = {}
        self._schema_cache: dict[frozenset[str] | None, list[dict]] = {}
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        input_model: type[BaseModel],
        allow_retry: bool = False,
        groups: set[str] | None = None,
        requires_approval: bool = False,
    ):
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            func=func,
            input_model=input_model,
            allow_retry=allow_retry,
            groups=set(groups) if groups is not None else None,
            requires_approval=requires_approval,

        )
        self._schema_cache.clear()

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def unregister(self, name: str) -> None:
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        del self._tools[name]
        self._schema_cache.clear()

    def list_tools(self) -> list[str]:
        return list(self._tools)

    def disable(self, name: str) -> None:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        self._tools[name] = replace(tool, enabled=False)
        self._schema_cache.clear()

    def enable(self, name: str) -> None:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        self._tools[name] = replace(tool, enabled=True)
        self._schema_cache.clear()

    def has_access(
        self,
        tool: ToolDefinition,
        groups: set[str] | None,
    ) -> bool:
        if not tool.enabled:
            return False
        if groups is None:
            return True
        if tool.groups is None:
            return False
        return bool(tool.groups.intersection(groups))

    def get_tool_schemas(self, groups: set[str] | None = None) -> list[dict]:
        cache_key = frozenset(groups) if groups is not None else None
        if cache_key in self._schema_cache:
            return deepcopy(self._schema_cache[cache_key])

        schemas = [] 

        for tool in self._tools.values():
            if not self.has_access(tool, groups):
                continue
                        
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_model.model_json_schema(),
                    },
                }
            )

        self._schema_cache[cache_key] = schemas
        return deepcopy(schemas)
    
    async def execute(
        self, name: str, arguments: dict, groups: set[str] | None = None
    ) -> ToolResult:
        tool = self.get(name)

        if tool is None:
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_NOT_FOUND,
                message="Tool not found.",
            )

        if not tool.enabled:
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_DISABLED,
                message="Tool is disabled.",
            )

        if not self.has_access(tool, groups):
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_GROUP_FORBIDDEN,
                message="Tool is not available to this group.",
            )

        for attempt in range(self.max_retries + 1):
            result = await self._execute_once(
                name, tool, arguments, attempts=attempt + 1
            )
            if (
                result.success
                or not result.retryable
                or not tool.allow_retry
                or attempt == self.max_retries
            ):
                return result
            max_delay = self.backoff_base_seconds * (2 ** attempt)
            delay = random.uniform(0, max_delay)
            logger.warning(
                "retrying tool request_id=%s name=%s in %.1f seconds (%s/%s)",
                request_id_var.get(), name, delay, attempt + 1, self.max_retries,
            )
            await asyncio.sleep(delay)

    def _duration_ms(self, start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 2)

    def _log_success(self, name: str, start: float, attempts: int) -> None:
        logger.info(
            "tool_execution %s",
            json.dumps({
                "request_id": request_id_var.get(),
                "tool": name,
                "success": True,
                "error": None,
                "attempts": attempts,
                "duration_ms": self._duration_ms(start),
            }),
        )

    def _log_failure(
        self,
        name: str,
        start: float,
        attempts: int,
        error: ToolErrorCode | None,
        exc_info: bool = False,
    ) -> None:
        logger.error(
            "tool_execution %s",
            json.dumps({
                "request_id": request_id_var.get(),
                "tool": name,
                "success": False,
                "error": error.value if error else None,
                "attempts": attempts,
                "duration_ms": self._duration_ms(start),
            }),
            exc_info=exc_info,
        )

    async def _execute_once(
        self, name: str, tool: ToolDefinition, arguments: dict, attempts: int
    ) -> ToolResult:
        start = time.perf_counter()

        try:
            validated = tool.input_model.model_validate(arguments)

            result = tool.func(
                **validated.model_dump()
            )
            if inspect.isawaitable(result):
                result = await asyncio.wait_for(result, timeout=self.timeout_seconds)

            self._log_success(name, start, attempts)
            return ToolResult(
                success=True,
                data=result,
            )

        except Exception as exc:
            tool_result = self._error_result(exc)
            self._log_failure(
                name, start, attempts, tool_result.error, exc_info=True
            )
            return tool_result

    def _error_result(self, exc: Exception) -> ToolResult:
        if isinstance(exc, ValidationError):
            return ToolResult(
                success=False,
                error=ToolErrorCode.INVALID_ARGUMENTS,
                message="Invalid tool arguments.",
            )
        if isinstance(exc, (TimeoutError, httpx.TimeoutException)):
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_TIMEOUT,
                message="Tool timed out.",
                retryable=True,
            )
        if isinstance(exc, httpx.HTTPStatusError):
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_HTTP_ERROR,
                message="External service returned an HTTP error.",
                retryable=exc.response.status_code >= 500
                or exc.response.status_code in (408, 429),
            )
        if isinstance(exc, httpx.RequestError):
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_NETWORK_ERROR,
                message="External service could not be reached.",
                retryable=True,
            )
        return ToolResult(
            success=False,
            error=ToolErrorCode.TOOL_EXECUTION_ERROR,
            message="Tool execution failed.",
        )

    def requires_approval(self, name: str) -> bool:
        # Return whether the tool requires human approval
        definition = self._tools.get(name)

        if definition is None:
            return False

        return definition.requires_approval