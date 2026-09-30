import pytest

from langgraph.checkpoint.memory import MemorySaver
from mcp import StdioServerParameters

from day03_python_engineering.api.dependencies import (
    create_agent,
    create_tool_registry,
)
from day03_python_engineering.mcp.provider import (
    MCPToolProvider,
)


@pytest.mark.asyncio
async def test_agent_can_use_mcp_tool() -> None:
    # Create an isolated registry containing the normal local tools
    registry = create_tool_registry()

    # Configure the local MCP server process
    server = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "day03_python_engineering.mcp.server",
        ],
    )

    # Keep the MCP client and server alive for the whole agent run
    async with MCPToolProvider(
        registry=registry,
        server=server,
    ):
        # Verify that MCP tool discovery registered the remote tool
        assert "get_server_time" in registry.list_tools()

        # Use an isolated in-memory checkpointer
        checkpointer = MemorySaver()

        # Inject the registry containing both local and MCP tools
        agent = create_agent(
            checkpointer=checkpointer,
            registry=registry,
        )

        # Ask the real agent to use the MCP server tool
        result = await agent.run(
            user_input=(
                "Use the get_server_time tool to get "
                "the current MCP server time."
            ),
            session_id="mcp-agent-integration",
        )

        # The workflow should complete normally
        assert result.status == "completed"

        # The agent should expose its runtime trace
        assert agent.last_trace is not None

        # Verify that the MCP tool actually reached execution
        tool_called = any(
            event["event"] == "tool_called"
            and event.get("tool") == "get_server_time"
            for event in agent.last_trace.events
        )

        assert tool_called is True

        # Verify that the MCP tool completed successfully
        tool_completed = any(
            event["event"] == "tool_completed"
            and event.get("tool") == "get_server_time"
            and event.get("success") is True
            for event in agent.last_trace.events
        )

        assert tool_completed is True