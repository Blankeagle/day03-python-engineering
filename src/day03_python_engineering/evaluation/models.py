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
    # Identify this evaluation case
    name: str

    # Store the tools selected by the planner
    actual_tools: list[str]

    # Store whether the workflow actually required approval
    actual_approval: bool

    # Indicate whether the selected tools match the expected tools
    tool_selection_correct: bool

    # Indicate whether the approval decision matches the expected behavior
    approval_correct: bool

    # Store the actual tool execution outcome.
    # None means that no tool execution completed.
    tool_execution_success: bool | None

    # Indicate whether the execution state is correct for this case
    execution_correct: bool

    # Indicate whether all evaluation checks passed
    passed: bool

@dataclass(slots=True, frozen=True)
class EvalSummary:
    # Store the total number of evaluated cases
    total_cases: int

    # Store the number of cases with correct tool selection
    tool_selection_correct: int

    # Store the number of cases with successful tool execution
    execution_correct: int

    # Store the number of cases with correct approval decisions
    approval_correct: int

    # Store the number of cases that passed every check
    passed_cases: int

    # Store the tool selection accuracy
    tool_selection_accuracy: float

    # Store the tool execution success rate
    execution_accuracy: float

    # Store the approval decision accuracy
    approval_accuracy: float

    # Store the overall case pass rate
    pass_rate: float