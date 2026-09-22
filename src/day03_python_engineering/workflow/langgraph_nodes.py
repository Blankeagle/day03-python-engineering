from collections.abc import Callable
from urllib import response

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_state import LangGraphState
from pydantic import BaseModel, Field

class ReviewResult(BaseModel):
    # Indicate whether the current plan step completed successfully
    success: bool

    # Explain why the step failed when success is false
    feedback: str


class PlanResult(BaseModel):
    # Store at least one executable plan step
    steps: list[str] = Field(min_length=1)

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
        user_message = state["original_request"]
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
                    "Return an execution plan that matches the required JSON schema. "
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
             # Force the planner output to match the plan schema
            format=PlanResult.model_json_schema(),
        )

        content = response["message"]["content"]

        plan_result = PlanResult.model_validate_json(content)

        return {
            "plan": plan_result.steps,
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
        # Protect the executor from an invalid plan position
        if current_step < 0 or current_step >= len(plan):
            raise ValueError(
                f"Invalid plan position: "
                f"current_step={current_step}, plan_length={len(plan)}"
            )

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

                    "Treat successful tool results as authoritative execution results. "
                    "Do not question, reinterpret, or speculate about whether a tool "
                    "result is real, current, simulated, or a placeholder. "

                    "If the workflow could not complete a plan step successfully, "
                    "clearly explain that limitation to the user. "
                    "Do not claim that a task was completed when it was not."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original request:\n"
                    f"{state['original_request']}\n\n"
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

def create_reviewer_node(
    client: OllamaClient,
) -> Callable:
    # Create a node that evaluates the result of the current plan step
    async def reviewer_node(state: LangGraphState) -> dict:
        current_step = state["current_step"]
        task = state["plan"][current_step]

        # Read the latest completed step result
        result = state["step_results"][-1]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. "
                    "Answer the user's original request using the completed "
                    "plan step results below. "
                    "Combine all relevant results into one clear answer. "
                    "If the workflow could not complete a plan step successfully, "
                    "clearly explain that limitation to the user. "
                    "Do not claim that a task was completed when it was not."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Plan step:\n{task}\n\n"
                    f"Execution result:\n{result}"
                ),
            },
        ]

        response = await client.chat(
            messages=messages,

            # Force the model output to match the review schema
            format=ReviewResult.model_json_schema(),
        )

        content = response["message"]["content"]

        review = ReviewResult.model_validate_json(content)

        return {
            "step_success": review.success,
            "review_feedback": review.feedback,
            "step": state["step"] + 1,
        }

    return reviewer_node


def create_replanner_node(
    client: OllamaClient,
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
) -> Callable:
    # Create a node that rebuilds the remaining plan after a failed step
    async def replanner_node(state: LangGraphState) -> dict:

        current_step = state["current_step"]

        # Keep steps that were already completed successfully
        completed_plan = state["plan"][:current_step]

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
                    "You are a replanning assistant. "
                    "The current plan step failed. "
                    "Create a new plan for the remaining work. "
                    "Do not repeat steps that were already completed. "
                    "Use the available tools when appropriate. "
                    f"Available tools: {tool_names}. "
                    "Return the new remaining execution plan using the required JSON schema."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original request:\n"
                    f"{state['original_request']}\n\n"
                    f"Failed step:\n"
                    f"{state['plan'][current_step]}\n\n"
                    f"Review feedback:\n"
                    f"{state['review_feedback']}"
                ),
            },
        ]
        response = await client.chat(
            messages=messages,

            # Force the replanner output to match the plan schema
            format=PlanResult.model_json_schema(),
        )

        content = response["message"]["content"]

        plan_result = PlanResult.model_validate_json(content)

        new_remaining_plan = plan_result.steps

        return {
        "plan": [
            *completed_plan,
            *new_remaining_plan,
        ],
        "step_success": True,
        "review_feedback": "",

        # Record one replanning attempt
        "replan_count": state["replan_count"] + 1,

        "step": state["step"] + 1,
    }

    return replanner_node

