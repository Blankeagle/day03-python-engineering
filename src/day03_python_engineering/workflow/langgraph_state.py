from typing import Any, TypedDict


class LangGraphState(TypedDict):
    # Store the conversation history shared across graph nodes
    messages: list[dict[str, Any]]

    # Store tool calls requested by the latest LLM response
    tool_calls: list[dict[str, Any]]

    # Track how many graph nodes have been executed
    step: int