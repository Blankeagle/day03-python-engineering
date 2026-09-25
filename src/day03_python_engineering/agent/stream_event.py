from dataclasses import dataclass
from typing import Any
import json

@dataclass(slots=True, frozen=True)
class AgentStreamEvent:
    # Identify the type of streaming event
    event: str

    # Store optional public data for this event
    data: dict[str, Any] | None = None

def map_stream_chunk(
    chunk: dict[str, Any],
) -> AgentStreamEvent | None:
    
    # Convert internal LangGraph updates into public streaming events
    if "planner" in chunk:
        return AgentStreamEvent(
            event="planning_completed",
        )

    if "executor" in chunk:
        return AgentStreamEvent(
            event="executing",
        )

    if "tool" in chunk:
        return AgentStreamEvent(
            event="tool_completed",
        )

    if "reviewer" in chunk:
        return AgentStreamEvent(
            event="reviewing_completed",
        )

    if "advance" in chunk:
        return AgentStreamEvent(
            event="step_completed",
        )

    if "final" in chunk:

        # Extract the final assistant answer from the workflow update
        messages = chunk["final"].get("messages", [])

        if not messages:
            return AgentStreamEvent(
                event="completed",
            )

        final_message = messages[-1]

        return AgentStreamEvent(
            event="completed",
            data={
                "answer": final_message.get("content", ""),
            },
        )

    # Ignore internal updates that are not part of the public API
    return None


def serialize_stream_event(
    event: AgentStreamEvent,
) -> str:
    # Serialize the event payload as JSON
    payload = {
        "data": event.data,
    }

    # Format the public event using the SSE protocol
    return (
        f"event: {event.event}\n"
        f"data: {json.dumps(payload)}\n\n"
    )