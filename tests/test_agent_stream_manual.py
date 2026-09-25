import pytest
from langgraph.checkpoint.memory import MemorySaver
from day03_python_engineering.agent.stream_event import AgentStreamEvent

from day03_python_engineering.api.dependencies import create_agent


@pytest.mark.asyncio
async def test_agent_stream_manual():
    # Use an in-memory checkpointer for the streaming test
    checkpointer = MemorySaver()

    # Create an agent without depending on Redis checkpoint storage
    agent = create_agent(
        checkpointer=checkpointer,
    )

    # Stream workflow updates as the agent runs
    async for chunk in agent.stream(
        user_message="Delete all my saved data.",
        session_id="stream-approval-test",
    ):
        print("STREAM CHUNK:", chunk)