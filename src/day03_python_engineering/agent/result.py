from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class AgentRunResult:
    # Describe whether the workflow completed or was interrupted
    status: str

    # Store the final answer when the workflow completes
    answer: str | None = None

    # Identify the workflow execution for checkpoint resume
    thread_id: str | None = None

    # Store interrupt information when the workflow is paused
    interrupt: Any | None = None