import pytest

from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.workflow.langgraph_nodes import create_reviewer_node


class FakeClient:
    async def chat(self, *args, **kwargs):
        # The reviewer should not call the LLM after a deterministic tool failure
        raise AssertionError("Reviewer LLM should not be called")


@pytest.mark.asyncio
async def test_reviewer_skips_llm_when_tool_failed():
    reviewer = create_reviewer_node(FakeClient())

    state = {
        "plan": ["Get the current time"],
        "current_step": 0,
        "step_results": ["Failed to get the current time."],
        "last_tool_success": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    result = await reviewer(state)

    assert result["step_success"] is False
    assert result["review_feedback"] == "The required tool execution failed."
    assert result["step"] == 1


@pytest.mark.asyncio
async def test_reviewer_uses_llm_when_tool_succeeded():
    class SuccessfulReviewClient:
        async def chat(self, *args, **kwargs):
            # Simulate a successful semantic review from the LLM
            return {
                "message": {
                    "content": (
                        '{"success": true, '
                        '"feedback": "The step was completed successfully."}'
                    )
                }
            }

    reviewer = create_reviewer_node(SuccessfulReviewClient())

    state = {
        "plan": ["Get the current time"],
        "current_step": 0,
        "step_results": ["The current time is 20:11."],
        "last_tool_success": True,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    result = await reviewer(state)

    assert result["step_success"] is True
    assert result["step"] == 1