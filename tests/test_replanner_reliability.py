import pytest

from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.workflow.langgraph_nodes import (
    create_replanner_node,
)


class FakeClient:
    async def chat(self, *args, **kwargs):
        # Return a deterministic replanned step
        return {
            "message": {
                "content": (
                    '{"steps": ["Try another approach"], '
                    '"tool_names": []}'
                )
            }
        }


class FakeRegistry:
    def get_tool_schemas(self, groups=None):
        # No tools are required for this test
        return []


@pytest.mark.asyncio
async def test_replanner_resets_last_tool_success():
    replanner = create_replanner_node(
        client=FakeClient(),
        registry=FakeRegistry(),
    )

    state = {
        "original_request": "Complete the task",
        "plan": ["Failed step"],
        "current_step": 0,
        "review_feedback": "The tool execution failed.",
        "replan_count": 0,
        "last_tool_success": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    result = await replanner(state)

    assert result["last_tool_success"] is None