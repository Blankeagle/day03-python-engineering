from day03_python_engineering.observability.trace import AgentTrace


def test_add_event() -> None:
    # Create a trace for one workflow execution
    trace = AgentTrace(
        thread_id="test-thread",
    )

    # Record one workflow event
    trace.add_event(
        "node_started",
        node="planner",
    )

    # Verify that the event was stored
    assert len(trace.events) == 1

    event = trace.events[0]

    assert event["event"] == "node_started"
    assert event["node"] == "planner"
    assert "timestamp" in event