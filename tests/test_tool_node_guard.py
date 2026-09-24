import pytest

from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_nodes import create_tool_node
from day03_python_engineering.observability.trace import AgentTrace
from pydantic import BaseModel


class DeleteSavedDataInput(BaseModel):
    pass


async def delete_saved_data() -> str:
    # Simulate a destructive action
    return "deleted"

@pytest.mark.asyncio
async def test_tool_node_blocks_unapproved_protected_tool():
    registry = ToolRegistry()



    registry.register(
        name="delete_saved_data",
        description="Delete saved data.",
        func=delete_saved_data,
        input_model=DeleteSavedDataInput,
        requires_approval=True,
    )

    tool_node = create_tool_node(
        registry=registry,
    )

    state = {
        "messages": [],
        "tool_calls": [
            {
                "function": {
                    "name": "delete_saved_data",
                    "arguments": {},
                }
            }
        ],
        "approval": False,
        "trace": AgentTrace(thread_id="test-thread"),

        "step": 0,
    }

    with pytest.raises(
        PermissionError,
        match="requires human approval",
    ):
        await tool_node(state)

@pytest.mark.asyncio
async def test_tool_node_allows_approved_protected_tool():
    registry = ToolRegistry()

    registry.register(
        name="delete_saved_data",
        description="Delete saved data.",
        func=delete_saved_data,
        input_model=DeleteSavedDataInput,
        requires_approval=True,
    )

    tool_node = create_tool_node(
        registry=registry,
    )

    state = {
        "messages": [],
        "tool_calls": [
            {
                "function": {
                    "name": "delete_saved_data",
                    "arguments": {},
                }
            }
        ],
        "approval": True,
        "trace": AgentTrace(thread_id="test-thread"),
        "step": 0,
    }

    result = await tool_node(state)

    assert result["tool_calls"] == []
    assert len(result["messages"]) == 1