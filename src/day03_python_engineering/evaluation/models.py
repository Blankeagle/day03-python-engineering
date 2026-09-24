from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class EvalCase:
    # Identify this evaluation case
    name: str

    # Store the user request sent to the agent
    input: str

    # Define the tools that the agent is expected to use
    expected_tools: list[str] = field(default_factory=list)

    # Define whether the workflow should require human approval
    expected_approval: bool = False


@dataclass(slots=True, frozen=True)
class EvalResult:
    # Identify the evaluation case
    name: str

    # Store the tools actually selected by the agent
    actual_tools: list[str]

    # Store whether the workflow actually required approval
    actual_approval: bool

    # Indicate whether all evaluation checks passed
    passed: bool
