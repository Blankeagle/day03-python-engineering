from collections.abc import Callable

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_state import LangGraphState


def create_llm_node(
    client: OllamaClient,
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
) -> Callable:
    # Create a node with access to the required dependencies
    async def llm_node(state: LangGraphState) -> dict:
        # Get the tool schemas available to this agent
        tools = registry.get_tool_schemas(
            groups=tool_groups,
        )

        # Call the LLM using the current conversation history
        response = await client.chat(
            messages=state["messages"],
            tools=tools,
        )

        assistant_message = response["message"]

        # Return only the state updates produced by this node
        return {
            "messages": [
                *state["messages"],
                assistant_message,
            ],
            "tool_calls": assistant_message.get(
                "tool_calls",
                [],
            ),
            "step": state["step"] + 1,
        }

    return llm_node


def create_tool_node(
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
) -> Callable:
    # Create a node that executes tool calls requested by the LLM
    async def tool_node(state: LangGraphState) -> dict:
        messages = list(state["messages"])

        # Execute every tool call requested by the latest LLM response
        for tool_call in state["tool_calls"]:
            function = tool_call["function"]

            tool_name = function["name"]
            arguments = function.get("arguments", {})

            # Delegate validation, timeout, and retry to ToolRegistry
            result = await registry.execute(
                name=tool_name,
                arguments=arguments,
                groups=tool_groups,
            )

            # Add the tool result to the conversation history
            messages.append(
                {
                    "role": "tool",
                    "content": result.model_dump_json(),
                }
            )

        # Return the updated state without mutating the input state
        return {
            "messages": messages,
            "tool_calls": [],
            "step": state["step"] + 1,
        }

    return tool_node