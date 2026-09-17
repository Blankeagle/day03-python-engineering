from langgraph.graph import END, START, StateGraph

from day03_python_engineering.workflow.langgraph_state import LangGraphState
from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry

from day03_python_engineering.workflow.langgraph_nodes import (
    create_llm_node,
    create_tool_node,
)


def create_agent_graph(
    client: OllamaClient,
    registry: ToolRegistry,
    tool_groups: set[str] | None = None,
):
    # Create a graph that uses LangGraphState as its shared state
    graph = StateGraph(LangGraphState)

 
    # Create the LLM node with the required dependencies
    llm_node = create_llm_node(
        client=client,
        registry=registry,
        tool_groups=tool_groups,
    )

    # Create the tool execution node
    tool_node = create_tool_node(
        registry=registry,
        tool_groups=tool_groups,
    )

    # Register the LLM node in the graph
    graph.add_node("llm", llm_node)

    # Register the tool node in the graph
    graph.add_node("tool", tool_node)

    # Define where graph execution starts
    graph.add_edge(START, "llm")

  # Route dynamically based on whether the LLM requested tools
    graph.add_conditional_edges(
        "llm",
        route_after_llm,
        {
            "tool": "tool",
            "end": END,
        },
    )
    # Return to the LLM after tool execution
    graph.add_edge("tool", "llm")

    # Compile the graph into an executable workflow
    return graph.compile()

def route_after_llm(state: LangGraphState) -> str:
    # Route to the tool node when the LLM requests tool execution
    if state["tool_calls"]:
        return "tool"

    # Finish the graph when no tool call is required
    return "end"