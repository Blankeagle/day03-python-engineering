import pytest

from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.tools.result import (
    ToolErrorCode,
    ToolResult,
)
from day03_python_engineering.workflow.langgraph_nodes import (
    create_tool_node,
)


class FakeRegistry:
    def requires_approval(self, name: str) -> bool:
        # No tool requires approval in this test
        return False

    async def execute(self, name: str, arguments: dict, groups=None) -> ToolResult:
        # Simulate the first tool failing
        if name == "tool_a":
            return ToolResult(
                success=False,
                error=ToolErrorCode.TOOL_EXECUTION_ERROR,
                message="Tool A failed.",
            )

        # Simulate the second tool succeeding
        return ToolResult(
            success=True,
            data="Tool B succeeded.",
        )


@pytest.mark.asyncio
async def test_tool_node_preserves_failure_across_multiple_tools():
    tool_node = create_tool_node(
        registry=FakeRegistry(),
    )

    state = {
        "messages": [],
        "tool_calls": [
            {
                "function": {
                    "name": "tool_a",
                    "arguments": {},
                }
            },
            {
                "function": {
                    "name": "tool_b",
                    "arguments": {},
                }
            },
        ],
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    result = await tool_node(state)

    # One failed tool should make the aggregated tool status fail
    assert result["last_tool_success"] is False


@pytest.mark.asyncio
async def test_tool_node_reports_success_when_all_tools_succeed():
    class SuccessfulRegistry:
        def requires_approval(self, name: str) -> bool:
            # No tool requires approval in this test
            return False

        async def execute(
            self,
            name: str,
            arguments: dict,
            groups=None,
        ) -> ToolResult:
            # Simulate every tool completing successfully
            return ToolResult(
                success=True,
                data=f"{name} succeeded.",
            )

    tool_node = create_tool_node(
        registry=SuccessfulRegistry(),
    )

    state = {
        "messages": [],
        "tool_calls": [
            {
                "function": {
                    "name": "tool_a",
                    "arguments": {},
                }
            },
            {
                "function": {
                    "name": "tool_b",
                    "arguments": {},
                }
            },
        ],
        "approval": False,
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    result = await tool_node(state)

    # All tools succeeded, so the aggregated status should succeed
    assert result["last_tool_success"] is True