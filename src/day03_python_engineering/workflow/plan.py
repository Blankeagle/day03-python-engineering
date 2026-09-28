from dataclasses import dataclass, field
from enum import StrEnum


class StepStatus(StrEnum):
    # The step has not started yet
    PENDING = "pending"

    # The step is currently being executed
    RUNNING = "running"

    # The step completed successfully
    COMPLETED = "completed" 

    # The step could not be completed
    FAILED = "failed"


@dataclass(slots=True)
class PlanStep:
    # Stable identifier for this plan step
    id: str

    # Human-readable task description
    description: str

    # Current execution state
    status: StepStatus = StepStatus.PENDING

    # Tools associated with this step
    tool_names: list[str] = field(default_factory=list)

    # Final result produced by this step
    result: str | None = None

    # Error information when execution fails
    error: str | None = None