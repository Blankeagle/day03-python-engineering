from dataclasses import dataclass
from typing import Any

from day03_python_engineering.evaluation.models import (
    EvalCase,
    EvalResult,
    EvalSummary,
)

from day03_python_engineering.observability.trace import AgentTrace

def evaluate_case(
    case: EvalCase,
    actual_tools: list[str],
    actual_approval: bool,
    tool_execution_success: bool | None = True,
) -> EvalResult:
    # Check whether the planner selected the expected tools
    tool_selection_correct = (
        actual_tools == case.expected_tools
    )

    # Check whether the approval decision matches the expected behavior
    approval_correct = (
        actual_approval == case.expected_approval
    )

    # Evaluate whether the execution state matches the expected workflow path
    if not case.expected_tools:
        # No-tool cases should not execute any tool
        execution_correct = (
            tool_execution_success is None
        )

    elif case.expected_approval:
        # Protected tools should stop before execution and wait for approval
        execution_correct = (
            actual_approval
            and tool_execution_success is None
        )

    else:
        # Normal tool cases should execute successfully
        execution_correct = (
            tool_execution_success is True
        )

    # The case passes only when every expected behavior is correct
    passed = (
        tool_selection_correct
        and approval_correct
        and execution_correct
    )

    return EvalResult(
        name=case.name,
        actual_tools=actual_tools,
        actual_approval=actual_approval,
        tool_selection_correct=tool_selection_correct,
        approval_correct=approval_correct,
        tool_execution_success=tool_execution_success,
        execution_correct=execution_correct,
        passed=passed,
    )

def summarize_results(
    results: list[EvalResult],
) -> EvalSummary:
    # Count the total number of evaluated cases
    total_cases = len(results)

    # Count successful checks for each evaluation dimension
    tool_selection_correct = sum(
        result.tool_selection_correct
        for result in results
    )

    execution_correct = sum(
        result.execution_correct
        for result in results
    )

    approval_correct = sum(
        result.approval_correct
        for result in results
    )

    passed_cases = sum(
        result.passed
        for result in results
    )

    # Avoid division by zero when no evaluation cases exist
    if total_cases == 0:
        return EvalSummary(
            total_cases=0,
            tool_selection_correct=0,
            execution_correct=0,
            approval_correct=0,
            passed_cases=0,
            tool_selection_accuracy=0.0,
            execution_accuracy=0.0,
            approval_accuracy=0.0,
            pass_rate=0.0,
        )

    # Calculate aggregate evaluation metrics
    return EvalSummary(
        total_cases=total_cases,
        tool_selection_correct=tool_selection_correct,
        execution_correct=execution_correct,
        approval_correct=approval_correct,
        passed_cases=passed_cases,
        tool_selection_accuracy=tool_selection_correct / total_cases,
        execution_accuracy=execution_correct / total_cases,
        approval_accuracy=approval_correct / total_cases,
        pass_rate=passed_cases / total_cases,
    )


@dataclass(slots=True, frozen=True)
class ActualBehavior:
    # Store the tools selected by the planner
    planned_tools: list[str]

    # Store the tools actually called during execution
    called_tools: list[str]

    # Store whether the workflow requested human approval
    approval_required: bool

    # Store tool execution status.
    # None means that no tool execution completed.
    tool_execution_success: bool | None

def extract_actual_behavior(
    trace: AgentTrace,
) -> ActualBehavior:
    # Collect tools selected by the planner
    planned_tools: list[str] = []

    # Collect tools that were actually called
    called_tools: list[str] = []

    # Track whether the workflow requested human approval
    approval_required = False

    # Collect completed tool execution results
    tool_execution_results: list[bool] = []

    for event in trace.events:
        # Read the tools selected by the planner
        if (
            event["event"] == "node_completed"
            and event.get("node") == "planner"
        ):
            planned_tools = list(
                event.get("tool_names", [])
            )

        # Record tools that actually reached execution
        if event["event"] == "tool_called":
            called_tools.append(
                event["tool"]
            )

        # Detect the real approval event emitted by the workflow
        if event["event"] == "approval_requested":
            approval_required = True

        # Record tool execution outcomes
        if event["event"] == "tool_completed":
            tool_execution_results.append(
                event["success"]
            )

    return ActualBehavior(
        planned_tools=planned_tools,
        called_tools=called_tools,
        approval_required=approval_required,
        # Distinguish "not executed" from successful execution
        tool_execution_success = (
            all(tool_execution_results)
            if tool_execution_results
            else None
        )
    )


def evaluate_trace(
    case: EvalCase,
    trace: AgentTrace,
) -> EvalResult:
    behavior = extract_actual_behavior(
        trace
    )

    return evaluate_case(
        case=case,
        actual_tools=behavior.planned_tools,
        actual_approval=behavior.approval_required,
        tool_execution_success=behavior.tool_execution_success,
    )