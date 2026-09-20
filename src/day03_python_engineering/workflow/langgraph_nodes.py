from collections.abc import Callable

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_state import LangGraphState


import json

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

def create_planner_node(
    client: OllamaClient,
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
) -> Callable:
    # Create a node that breaks a complex request into executable steps
    async def planner_node(state: LangGraphState) -> dict:
        user_message = state["messages"][-1]["content"]

        tools = registry.get_tool_schemas(
            groups=tool_groups,
        )

        tool_names = [
            tool["function"]["name"]
            for tool in tools
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a planning assistant. "
                    "Break the user's request into a short execution plan. "
                    "Use the available tools when appropriate. "
                    f"Available tools: {tool_names}. "
                    "Do not invent tool limitations when a suitable tool exists. "
                    "Return only a JSON array of strings. "
                    "Do not answer the user's request."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        response = await client.chat(
            messages=messages,
        )

        content = response["message"]["content"]
        plan = json.loads(content)

        return {
            "plan": plan,
            "current_step": 0,
            "step": state["step"] + 1,
        }

    return planner_node

def create_executor_node(
    client: OllamaClient,
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
) -> Callable:
    # Create a node that executes the current item in the plan
    async def executor_node(state: LangGraphState) -> dict:
        current_step = state["current_step"]
        plan = state["plan"]
        task = plan[current_step]

        messages = list(state["messages"])

        # Check whether this execution is continuing after a tool result
        has_tool_result = (
            bool(messages)
            and messages[-1].get("role") == "tool"
        )

        if has_tool_result:
            # Finish the current plan step using the tool result only
            response = await client.chat(
                messages=[
                    *messages,
                    {
                        "role": "user",
                        "content": (
                            "Use the tool result above to finish only "
                            "the current plan step. "
                            "Do not execute any other plan step."
                        ),
                    },
                ],
            )
        else:
            # Start executing a new plan step
            tools = registry.get_tool_schemas(
                groups=tool_groups,
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Execute only the following step from the plan.\n"
                        "Do not execute other plan steps yet.\n"
                        "Use only the tools required for this specific step.\n\n"
                        f"Current step:\n{task}"
                    ),
                }
            )

            response = await client.chat(
                messages=messages,
                tools=tools,
            )

        assistant_message = response["message"]

        tool_calls = assistant_message.get(
            "tool_calls",
            [],
        )

        step_results = list(state["step_results"])

        # Save the result only when the current plan step is complete
        if not tool_calls:
            result = assistant_message.get("content", "")

            if result:
                step_results.append(result)

        return {
            "messages": [
                *messages,
                assistant_message,
            ],
            "tool_calls": tool_calls,
            "step_results": step_results,
            "step": state["step"] + 1,
        }

    return executor_node


def advance_plan_node(
    state: LangGraphState,
) -> dict:
    # Move to the next item in the execution plan
    return {
        "current_step": state["current_step"] + 1,
        "step": state["step"] + 1,
    }



def create_final_node(
    client: OllamaClient,
) -> Callable:
    # Create a node that combines completed plan results
    async def final_node(state: LangGraphState) -> dict:
        results = "\n\n".join(
            state["step_results"]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. "
                    "Answer the user's original request using the completed "
                    "plan step results below. "
                    "Combine all relevant results into one clear answer. "
                    "Do not ignore any result that is needed to answer "
                    "the original request."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original request:\n"
                    f"{state['messages'][1]['content']}\n\n"
                    f"Completed step results:\n"
                    f"{results}"
                ),
            },
        ]

        # Generate one final answer from all completed step results
        response = await client.chat(
            messages=messages,
        )

        assistant_message = response["message"]

        return {
            "messages": [
                *state["messages"],
                assistant_message,
            ],
            "tool_calls": [],
            "step": state["step"] + 1,
        }

    return final_node