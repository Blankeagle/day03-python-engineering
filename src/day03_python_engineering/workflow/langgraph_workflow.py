from langgraph.graph import END, START, StateGraph

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_nodes import (
    advance_plan_node,
    create_executor_node,
    create_final_node,
    create_planner_node,
    create_tool_node,
)
from day03_python_engineering.workflow.langgraph_state import LangGraphState


def route_after_executor(state: LangGraphState) -> str:
    # Execute tools when the current plan step requires tool calls
    if state["tool_calls"]:
        return "tool"

    # The current plan step is complete
    return "next_step"


def route_after_advance(state: LangGraphState) -> str:
    # Continue when there are still plan items to execute
    if state["current_step"] < len(state["plan"]):
        return "executor"

    # All plan items have been completed
    return "final"


def create_agent_graph(
    client: OllamaClient,
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
):
    # Create the graph with shared agent state
    graph = StateGraph(LangGraphState)

    # Create workflow nodes
    planner_node = create_planner_node(
        client=client,
        registry=registry,
        tool_groups=tool_groups,
    )

    executor_node = create_executor_node(
        client=client,
        registry=registry,
        tool_groups=tool_groups,
    )

    tool_node = create_tool_node(
        registry=registry,
        tool_groups=tool_groups,
    )

    final_node = create_final_node(
        client=client,
    )

    # Register workflow nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("tool", tool_node)
    graph.add_node("advance", advance_plan_node)
    graph.add_node("final", final_node)

    # Start by generating an execution plan
    graph.add_edge(START, "planner")

    # Execute the first plan item
    graph.add_edge("planner", "executor")

    # Decide whether the executor needs a tool
    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "tool": "tool",
            "next_step": "advance",
        },
    )

    # Continue the same plan item after tool execution
    graph.add_edge("tool", "executor")

    # Continue with the next plan item or generate the final answer
    graph.add_conditional_edges(
        "advance",
        route_after_advance,
        {
            "executor": "executor",
            "final": "final",
        },
    )

    # Finish after generating the final answer
    graph.add_edge("final", END)

    # Compile the graph into an executable workflow
    return graph.compile()