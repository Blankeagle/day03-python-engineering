import pytest

from day03_python_engineering.exceptions import InvalidAgentOutputError
from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.workflow.langgraph_nodes import (
    create_final_node,
)
from day03_python_engineering.workflow.plan import PlanStep,StepStatus


from day03_python_engineering.workflow.langgraph_nodes import (
    build_final_context,
    build_memory_context,
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
        "plan": [
            PlanStep(
                id="step_1",
                description="Get the current time.",
                status=StepStatus.COMPLETED,
                tool_names=["get_current_time"],
                result="The current time is 10:00.",
            )
        ],
        "messages": [],
        "requires_approval": False,
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
        "user_memory": "",
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
        "plan": [
            PlanStep(
                id="step_1",
                description="Get the current time.",
                status=StepStatus.COMPLETED,
                tool_names=["get_current_time"],
                result="The current time is 10:00.",
            )
        ],
        "messages": [],
        "requires_approval": False,
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
        "user_memory": "",
    }

    result = await final_node(state)

    assert result["messages"][-1]["content"] == "The current time is 10:00."
    assert result["step"] == 1


def test_build_memory_context_includes_user_memory():
    context = build_memory_context(
        "The user prefers concise explanations."
    )

    assert "Long-term information about the user:" in context
    assert "The user prefers concise explanations." in context
    assert "only when it is relevant" in context

def test_build_memory_context_returns_empty_string_for_empty_memory():
    context = build_memory_context("")

    assert context == ""