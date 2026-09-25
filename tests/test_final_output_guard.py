import pytest

from day03_python_engineering.exceptions import InvalidAgentOutputError
from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.workflow.langgraph_nodes import (
    create_final_node,
)


class EmptyOutputClient:
    async def chat_stream(self, *args, **kwargs):
        # Simulate an empty streamed final response from the LLM
        if False:
            yield ""


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


@pytest.mark.asyncio
async def test_final_node_accepts_valid_output():
    class ValidOutputClient:
        async def chat_stream(self, *args, **kwargs):
            # Simulate a valid streamed final response from the LLM
            yield "The current time is 10:00."

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