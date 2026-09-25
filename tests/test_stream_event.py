from day03_python_engineering.agent.stream_event import (
    AgentStreamEvent,
    map_stream_chunk,
    serialize_stream_event,
)

def test_serialize_completed_stream_event():
    # Create a completed public stream event
    event = AgentStreamEvent(
        event="completed",
        data={
            "answer": "Hello",
        },
    )

    # Serialize the event using the SSE protocol
    result = serialize_stream_event(event)

    assert "event: completed\n" in result
    assert '"answer": "Hello"' in result
    assert result.endswith("\n\n")

def test_map_stream_chunk_hides_internal_state():
    # Simulate an internal LangGraph tool update
    chunk = {
        "tool": {
            "messages": [
                {
                    "role": "tool",
                    "content": "internal tool result",
                }
            ],
            "last_tool_success": True,
        }
    }

    event = map_stream_chunk(chunk)

    assert event is not None
    assert event.event == "tool_completed"
    assert event.data is None

def test_map_stream_chunk_ignores_unknown_node():
    # Simulate an internal node that is not part of the public API
    chunk = {
        "internal_node": {
            "secret": "internal data",
        }
    }

    event = map_stream_chunk(chunk)

    assert event is None

def test_map_final_chunk_includes_answer():
    # Simulate the final LangGraph update
    chunk = {
        "final": {
            "messages": [
                {
                    "role": "assistant",
                    "content": "The current time is 12:30 PM.",
                }
            ]
        }
    }

    event = map_stream_chunk(chunk)

    assert event is not None
    assert event.event == "completed"
    assert event.data == {
        "answer": "The current time is 12:30 PM.",
    }