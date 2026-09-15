from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
import logging
import json
from uuid import uuid4

from day03_python_engineering.request_context import request_id_var
from day03_python_engineering.tools.result import ToolErrorCode, ToolResult

logger = logging.getLogger(__name__)

class Agent:
    def __init__(
        self,
        client: OllamaClient,
        registry: ToolRegistry,
        tool_groups: set[str] | None = None,
        max_steps: int = 10,
        max_messages: int = 20,
    ):
        self.client = client
        self.registry = registry
        self.tool_groups = set(tool_groups) if tool_groups is not None else None
        self.max_steps = max_steps
        self.max_messages = max_messages
    

        self.base_system_prompt = (
            "You are a helpful AI assistant."
        )

        self.messages = [
            {
                "role": "system",
                "content": self.base_system_prompt,
            }
        ]

    async def run(self, user_input: str) -> str:
        token = None
        if request_id_var.get() is None:
            token = request_id_var.set(uuid4().hex)

        try:
            return await self._run(user_input)
        finally:
            if token is not None:
                request_id_var.reset(token)

    async def _run(self, user_input: str) -> str:
        self.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )
        self._trim_messages()

        for step in range(self.max_steps):
            response = await self.client.chat(
                messages=self.messages,
                tools=self.registry.get_tool_schemas(groups=self.tool_groups),
                )

            message = response["message"]

            self.messages.append(message)

            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                return message["content"]

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]

                arguments = tool_call["function"].get(
                    "arguments",
                    {},
                )

                try:
                    result = await self.registry.execute(
                        tool_name,
                        arguments,
                        groups=self.tool_groups,
                    )

                except Exception:
                    logger.exception("tool %s failed outside registry", tool_name)
                    result = ToolResult(
                        success=False,
                        error=ToolErrorCode.TOOL_EXECUTION_ERROR,
                        message="Tool execution failed.",
                    )

                logger.info(
                    "agent step=%s tool=%s arguments=%s result=%s",
                    step + 1,
                    tool_name,
                    arguments,
                    result,
                )

                self.messages.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "content": result.model_dump_json()
                    }
                )

        return "Agent 超过最大执行步数，任务未完成。"

    def _trim_messages(self):
        if len(self.messages) <= self.max_messages + 1:
            return

        system_message = self.messages[0]

        recent_messages = self.messages[-self.max_messages:]

        self.messages = [
            system_message,
            *recent_messages,
        ]

    def set_user_memory(
        self,
        memory_prompt: str,
    ) -> None:
        content = self.base_system_prompt

        if memory_prompt:
            content += (
                "\n\nLong-term information about the user:\n"
                f"{memory_prompt}\n\n"
                "Use the long-term user information above when the user "
                "asks about themselves. "
                "Do not search the knowledge base for information that is "
                "already available in the user's long-term memory."
            )

        self.messages[0]["content"] = content