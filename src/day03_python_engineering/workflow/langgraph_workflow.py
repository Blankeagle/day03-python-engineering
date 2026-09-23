from langgraph.graph import END, START, StateGraph

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_nodes import (
    advance_plan_node,
    create_executor_node,
    create_final_node,
    create_planner_node,
    create_replanner_node,
    create_reviewer_node,
    create_tool_node,
    approval_node,

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
    checkpointer,
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

    reviewer_node = create_reviewer_node(
        client=client,
    )

    replanner_node = create_replanner_node(
        client=client,
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
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("replanner", replanner_node)
    # Pause the workflow for user approval before execution
    graph.add_node("approval", approval_node)

    # Start by generating an execution plan
    graph.add_edge(START, "planner")

 # Route the plan based on whether human approval is required
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "approval": "approval",
            "executor": "executor",
        },
    )

    # Route the workflow based on the user's approval decision
    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "executor": "executor",
            "final": "final",
        },
    )
    # Decide whether the executor needs a tool
    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "tool": "tool",
            "next_step": "reviewer",
        },
    )

    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "advance": "advance",
            "replan": "replanner",
            "final": "final",
        },
    )

    graph.add_conditional_edges(
        "replanner",
        route_after_replanner,
        {
            "executor": "executor",
            "final": "final",
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
    return graph.compile(
        checkpointer=checkpointer,
    )


def route_after_review(state: LangGraphState) -> str:
    # Continue normally when the current plan step passed review
    if state["step_success"]:
        return "advance"

    # Stop replanning after reaching the retry limit

    if state["replan_count"] >= 2:
        return "final"

    # Replan when the current step failed review
    return "replan"

def route_after_replanner(state: LangGraphState) -> str:
    # Continue only when the replanned workflow has work left to execute
    if state["current_step"] < len(state["plan"]):
        return "executor"

    # Finish safely when there are no remaining plan steps
    return "final"

def route_after_approval(state: LangGraphState) -> str:
    # Continue execution only when the user approved the plan
    if state["approval"]:
        return "executor"

    # Stop the workflow when the user rejected the plan
    return "final"

    # Decide required approval 
def route_after_planner(state: LangGraphState) -> str:
    # Require human approval only for plans with meaningful side effects
    if state["requires_approval"]:
        return "approval"

    # Continue directly for read-only or low-risk plans
    return "executor"