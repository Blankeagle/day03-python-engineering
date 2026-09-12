from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry


class Agent:
    def __init__(
        self,
        client: OllamaClient,
        registry: ToolRegistry,
        tools: list[dict],
        max_steps: int = 10,
        max_messages: int = 20,
    ):
        self.client = client
        self.registry = registry
        self.tools = tools
        self.max_steps = max_steps
        self.max_messages = max_messages

        self.messages = [
            {
                "role": "system",
                "content": "你是一个有帮助的 AI 助手。",
            }
        ]

    def run(self, user_input: str) -> str:
        self.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )
        self._trim_messages()

        for step in range(self.max_steps):
            response = self.client.chat(
                messages=self.messages,
                tools=self.tools,
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
                    result = self.registry.execute(
                        tool_name,
                        arguments,
                    )

                except Exception as e:
                    result = f"工具执行失败: {str(e)}"

                print(
                    f"[Step {step + 1}] "
                    f"工具: {tool_name}, "
                    f"参数: {arguments}, "
                    f"结果: {result}"
                )

                self.messages.append(
                    {
                        "role": "tool",
                        "content": str(result),
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
