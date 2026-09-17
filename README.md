# Day 11 — LangGraph Workflow Migration

## Goal

The goal of Day 11 was to migrate the agent orchestration layer from a manually implemented workflow to LangGraph.

The existing components were kept unchanged:

- OllamaClient
- ToolRegistry
- RAGService
- ChromaVectorStore
- Session Memory
- Long-term User Memory
- FastAPI API layer

LangGraph is responsible only for controlling the agent workflow.

---

## Architecture

The current agent workflow is:

    User
      |
      v
    FastAPI
      |
      v
    Agent
      |
      v
    LangGraph
      |
      v
    START
      |
      v
    LLM Node
      |
      v
    Conditional Edge
      |
      +--------------------+
      |                    |
      | tool_calls         | no tool_calls
      v                    v
    Tool Node             END
      |
      v
    ToolRegistry
      |
      +--> Time Tool
      |
      +--> Weather Tool
      |
      +--> RAG Tool
             |
             v
          RAGService
             |
             v
           Chroma
      |
      v
    LLM Node

The main execution loop is:

    LLM -> Tool -> LLM -> ... -> END

---

## 1. LangGraph State

LangGraph uses a shared state that is passed between graph nodes.

```python
from typing import Any, TypedDict


class LangGraphState(TypedDict):
    # Store the conversation history shared across graph nodes
    messages: list[dict[str, Any]]

    # Store tool calls requested by the latest LLM response
    tool_calls: list[dict[str, Any]]

    # Track how many graph nodes have been executed
    step: int