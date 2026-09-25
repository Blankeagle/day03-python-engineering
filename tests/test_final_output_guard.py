import pytest

from day03_python_engineering.exceptions import InvalidAgentOutputError
from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.workflow.langgraph_nodes import (
    create_final_node,
)


class EmptyOutputClient:
    async def chat(self, *args, **kwargs):
        # Simulate an empty final response from the LLM
        return {
            "message": {
                "role": "assistant",
                "content": "   ",
            }
        }


@pytest.mark.asyncio
async def test_final_node_rejects_empty_output():
    final_node = create_final_node(
        client=EmptyOutputClient(),
    )

    state = {
        "original_request": "What time is it?",
        "step_results": ["The current time is 10:00."],
        "messages": [],
        "requires_approval": False,
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    with pytest.raises(
        InvalidAgentOutputError,
        match="invalid final answer",
    ):
        await final_node(state)

    failed_events = [
        event
        for event in state["trace"].events
        if event["event"] == "node_failed"
    ]

    assert len(failed_events) == 1
    assert failed_events[0]["node"] == "final"
    assert failed_events[0]["error_type"] == "InvalidAgentOutputError"    




@pytest.mark.asyncio
async def test_final_node_accepts_valid_output():
    class ValidOutputClient:
        async def chat(self, *args, **kwargs):
            # Simulate a valid final response from the LLM
            return {
                "message": {
                    "role": "assistant",
                    "content": "The current time is 10:00.",
                }
            }

    final_node = create_final_node(
        client=ValidOutputClient(),
    )

    state = {
        "original_request": "What time is it?",
        "step_results": ["The current time is 10:00."],
        "messages": [],
        "requires_approval": False,
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    result = await final_node(state)

    assert result["messages"][-1]["content"] == "The current time is 10:00."
    assert result["step"] == 1





@pytest.mark.asyncio
async def test_final_node_rejects_non_string_output():
    class InvalidOutputClient:
        async def chat(self, *args, **kwargs):
            # Simulate an invalid non-string response from the LLM
            return {
                "message": {
                    "role": "assistant",
                    "content": None,
                }
            }

    final_node = create_final_node(
        client=InvalidOutputClient(),
    )

    state = {
        "original_request": "What time is it?",
        "step_results": ["The current time is 10:00."],
        "messages": [],
        "requires_approval": False,
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    with pytest.raises(
        InvalidAgentOutputError,
        match="invalid final answer",
    ):
        await final_node(state)