import pytest

from day03_python_engineering.observability.trace import AgentTrace
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.workflow.langgraph_nodes import (
    create_planner_node,
)


class CapturingPlannerClient:
    def __init__(self):
        self.messages = None

    async def chat(self, *args, **kwargs):
        # Capture the context sent to the planner
        self.messages = kwargs["messages"]

        return {
            "message": {
                "content": (
                    '{"steps":["Compare RDB and AOF."],'
                    '"tool_names":[]}'
                )
            }
        }


@pytest.mark.asyncio
async def test_planner_receives_recent_conversation_context():
    client = CapturingPlannerClient()
    registry = ToolRegistry()

    planner_node = create_planner_node(
        client=client,
        registry=registry,
    )

    state = {
        "original_request": "What are the differences?",
        "conversation_messages": [
            {
                "role": "user",
                "content": "Tell me about Redis persistence.",
            },
            {
                "role": "assistant",
                "content": "Redis supports RDB and AOF.",
            },
            {
                "role": "user",
                "content": "What are the differences?",
            },
        ],
        "user_memory": "",
        "messages": [],
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }


    await planner_node(state)

    assert client.messages is not None

    # The planner should receive the recent conversation
    assert client.messages[1:] == state["conversation_messages"]

    # The latest user request should appear only once
    latest_request_count = sum(
        1
        for message in client.messages
        if message.get("content") == "What are the differences?"
    )

    assert latest_request_count == 1


@pytest.mark.asyncio
async def test_planner_limits_conversation_context():
    client = CapturingPlannerClient()
    registry = ToolRegistry()

    planner_node = create_planner_node(
        client=client,
        registry=registry,
    )

    conversation_messages = [
        {
            "role": "user",
            "content": f"message-{index}",
        }
        for index in range(10)
    ]

    state = {
        "original_request": "message-9",
        "conversation_messages": conversation_messages,
        "messages": [],
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
        "user_memory": "",
    }

    await planner_node(state)

    assert client.messages is not None

    # The system prompt is followed by only the latest 6 conversation messages
    assert len(client.messages) == 7

    assert client.messages[1:] == conversation_messages[-6:]

    # Older conversation context should not be sent to the planner
    assert all(
        message.get("content") != "message-0"
        for message in client.messages
    )

@pytest.mark.asyncio
async def test_planner_receives_user_memory():
    client = CapturingPlannerClient()
    registry = ToolRegistry()

    planner_node = create_planner_node(
        client=client,
        registry=registry,
    )

    state = {
        "original_request": "What should I learn next?",
        "user_memory": "The user is learning AI agent engineering.",
        "conversation_messages": [
            {
                "role": "user",
                "content": "What should I learn next?",
            },
        ],
        "messages": [],
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    await planner_node(state)

    system_content = client.messages[0]["content"]

    assert "Long-term information about the user:" in system_content
    assert "The user is learning AI agent engineering." in system_content


@pytest.mark.asyncio
async def test_planner_omits_empty_user_memory():
    client = CapturingPlannerClient()
    registry = ToolRegistry()

    planner_node = create_planner_node(
        client=client,
        registry=registry,
    )

    state = {
        "original_request": "What time is it?",
        "user_memory": "",
        "conversation_messages": [
            {
                "role": "user",
                "content": "What time is it?",
            },
        ],
        "messages": [],
        "step": 0,
        "trace": AgentTrace(thread_id="test-thread"),
    }

    await planner_node(state)

    system_content = client.messages[0]["content"]

    assert "Long-term information about the user:" not in system_content