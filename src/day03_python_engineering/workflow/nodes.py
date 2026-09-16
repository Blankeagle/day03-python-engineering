from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.workflow.state import AgentState
from src.day03_python_engineering.tools.registry import ToolRegistry


class LLMNode:
    def __init__(
        self,
        client: OllamaClient,
        registry: ToolRegistry,
        tool_groups: set[str] | None = None,
    ):
        self.client = client
        self.registry = registry
        self.tool_groups = tool_groups

    async def run(self, state: AgentState) -> AgentState:
        response = await self.client.chat(
            messages=state.messages,
            tools=self.registry.get_tool_schemas(
                groups=self.tool_groups,
            ),
        )

        assistant_message = response["message"]

        state.messages.append(assistant_message)

        state.tool_calls = assistant_message.get(
            "tool_calls",
            []
        )

        state.step += 1

        return state


class ToolNode:
    def __init__(
        self,
        registry: ToolRegistry,
        tool_groups: set[str] | None = None,
    ):
        self.registry = registry
        self.tool_groups = tool_groups

    async def run(self, state: AgentState) -> AgentState:
        # Execute every tool requested by the LLM
        for tool_call in state.tool_calls:
            function = tool_call["function"]

            tool_name = function["name"]
            arguments = function.get("arguments", {})

            # Execute the tool through the registry
            result = await self.registry.execute(
                name=tool_name,
                arguments=arguments,
                groups=self.tool_groups,
            )

            # Add the tool result to the conversation
            state.messages.append(
                {
                    "role": "tool",
                    "content": result.model_dump_json(),
                }
            )

        # Clear completed tool calls
        state.tool_calls = []

        # Record one completed workflow step
        state.step += 1

        return state