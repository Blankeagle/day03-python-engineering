from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    # Conversation history shared across workflow nodes
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Number of workflow nodes executed
    step: int = 0

    # Tool calls requested by the latest LLM response
    tool_calls: list[dict[str, Any]] = field(default_factory=list)