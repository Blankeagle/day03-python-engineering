import pytest

from day03_python_engineering.evaluation.evaluator import (
    evaluate_case,
    evaluate_trace,
    extract_actual_behavior,
    summarize_results,
)
from day03_python_engineering.evaluation.models import (
    EvalCase,
    EvalResult,
)
from day03_python_engineering.observability.trace import AgentTrace


def test_evaluate_case_passes_when_actual_matches_expected() -> None:
    # Define the expected agent behavior
    case = EvalCase(
        name="current_time",
        input="What time is it now?",
        expected_tools=["get_current_time"],
        expected_approval=False,
    )

    # Evaluate matching actual behavior
    result = evaluate_case(
        case=case,
        actual_tools=["get_current_time"],
        actual_approval=False,
        tool_execution_success=True,
    )

    assert result.name == "current_time"
    assert result.actual_tools == ["get_current_time"]
    assert result.actual_approval is False
    assert result.tool_selection_correct is True
    assert result.approval_correct is True
    assert result.tool_execution_success is True
    assert result.execution_correct is True
    assert result.passed is True

def test_evaluate_case_fails_when_tool_does_not_match() -> None:
    # Define the expected agent behavior
    case = EvalCase(
        name="current_time",
        input="What time is it now?",
        expected_tools=["get_current_time"],
        expected_approval=False,
    )

    # Evaluate behavior with the wrong tool,
    # but assume that the selected tool executed successfully
    result = evaluate_case(
        case=case,
        actual_tools=["get_weather"],
        actual_approval=False,
        tool_execution_success=True,
    )

    assert result.tool_selection_correct is False
    assert result.approval_correct is True
    assert result.execution_correct is True
    assert result.passed is False


def test_evaluate_case_fails_when_approval_does_not_match() -> None:
    case = EvalCase(
        name="delete_data",
        input="Delete all my saved data.",
        expected_tools=["delete_saved_data"],
        expected_approval=True,
    )

    result = evaluate_case(
        case=case,
        actual_tools=["delete_saved_data"],
        actual_approval=False,
    )

    assert result.tool_selection_correct is True
    assert result.approval_correct is False
    assert result.execution_correct is False
    assert result.passed is False


def test_summarize_results_calculates_metrics() -> None:
    results = [
        EvalResult(
            name="case_1",
            actual_tools=["get_current_time"],
            actual_approval=False,
            tool_selection_correct=True,
            approval_correct=True,
            tool_execution_success=True,
            execution_correct=True,
            passed=True,
        ),
        EvalResult(
            name="case_2",
            actual_tools=["get_weather"],
            actual_approval=False,
            tool_selection_correct=False,
            approval_correct=True,
            execution_correct=True,
            passed=False,
            tool_execution_success=True,
        ),
        EvalResult(
            name="case_3",
            actual_tools=["delete_saved_data"],
            actual_approval=True,
            tool_selection_correct=True,
            approval_correct=True,
            tool_execution_success=None,
            execution_correct=True,
            passed=True,
        ),
    ]

    summary = summarize_results(results)

    assert summary.total_cases == 3

    assert summary.tool_selection_correct == 2
    assert summary.tool_selection_accuracy == pytest.approx(2 / 3)

    assert summary.execution_correct == 3
    assert summary.execution_accuracy == pytest.approx(1.0)

    assert summary.approval_correct == 3
    assert summary.approval_accuracy == pytest.approx(1.0)

    assert summary.passed_cases == 2
    assert summary.pass_rate == pytest.approx(2 / 3)


def test_extract_actual_behavior_from_trace() -> None:
    trace = AgentTrace(
        thread_id="test-thread",
    )

    # Simulate the planner selecting the tool
    trace.add_event(
        "node_completed",
        node="planner",
        plan=["Delete all saved data."],
        tool_names=["delete_saved_data"],
    )

    # Simulate the workflow requesting human approval
    trace.add_event(
        "approval_requested",
    )

    # Simulate the tool actually being called after approval
    trace.add_event(
        "tool_called",
        tool="delete_saved_data",
    )

    trace.add_event(
        "tool_completed",
        tool="delete_saved_data",
        success=True,
    )

    behavior = extract_actual_behavior(trace)

    assert behavior.planned_tools == [
        "delete_saved_data",
    ]

    assert behavior.called_tools == [
        "delete_saved_data",
    ]

    assert behavior.approval_required is True
    assert behavior.tool_execution_success is True


def test_extract_actual_behavior_without_approval() -> None:
    trace = AgentTrace(
        thread_id="test-thread",
    )

    trace.add_event(
        "node_completed",
        node="planner",
        plan=["Get the current time."],
        tool_names=["get_current_time"],
    )

    trace.add_event(
        "tool_called",
        tool="get_current_time",
    )

    trace.add_event(
        "tool_completed",
        tool="get_current_time",
        success=True,
    )

    behavior = extract_actual_behavior(trace)

    assert behavior.planned_tools == [
        "get_current_time",
    ]

    assert behavior.called_tools == [
        "get_current_time",
    ]

    assert behavior.approval_required is False
    assert behavior.tool_execution_success is True


def test_extract_actual_behavior_detects_tool_failure() -> None:
    trace = AgentTrace(
        thread_id="test-thread",
    )

    trace.add_event(
        "node_completed",
        node="planner",
        plan=["Get the current time."],
        tool_names=["get_current_time"],
    )

    trace.add_event(
        "tool_called",
        tool="get_current_time",
    )

    trace.add_event(
        "tool_completed",
        tool="get_current_time",
        success=False,
    )

    behavior = extract_actual_behavior(trace)

    assert behavior.planned_tools == [
        "get_current_time",
    ]

    assert behavior.called_tools == [
        "get_current_time",
    ]

    assert behavior.approval_required is False
    assert behavior.tool_execution_success is False


def test_extract_actual_behavior_without_tool_calls() -> None:
    trace = AgentTrace(
        thread_id="test-thread",
    )

    trace.add_event(
        "node_completed",
        node="planner",
        plan=[],
        tool_names=[],
    )

    behavior = extract_actual_behavior(trace)

    assert behavior.planned_tools == []
    assert behavior.called_tools == []
    assert behavior.approval_required is False
    assert behavior.tool_execution_success is None


def test_summarize_results_handles_empty_results() -> None:
    summary = summarize_results([])

    assert summary.total_cases == 0

    assert summary.tool_selection_correct == 0
    assert summary.execution_correct == 0
    assert summary.approval_correct == 0
    assert summary.passed_cases == 0

    assert summary.tool_selection_accuracy == 0.0
    assert summary.execution_accuracy == 0.0
    assert summary.approval_accuracy == 0.0
    assert summary.pass_rate == 0.0


def test_evaluate_trace_uses_actual_runtime_behavior() -> None:
    case = EvalCase(
        name="current_time",
        input="What time is it now?",
        expected_tools=["get_current_time"],
        expected_approval=False,
    )

    trace = AgentTrace(
        thread_id="test-thread",
    )

    # Simulate the tool selected by the planner
    trace.add_event(
        "node_completed",
        node="planner",
        plan=["Get the current time."],
        tool_names=["get_current_time"],
    )

    # Simulate the tool actually reaching execution
    trace.add_event(
        "tool_called",
        tool="get_current_time",
    )

    # Simulate successful tool execution
    trace.add_event(
        "tool_completed",
        tool="get_current_time",
        success=True,
    )

    result = evaluate_trace(
        case=case,
        trace=trace,
    )

    assert result.actual_tools == [
        "get_current_time",
    ]

    assert result.actual_approval is False

    assert result.tool_selection_correct is True
    assert result.tool_execution_success is True
    assert result.execution_correct is True
    assert result.approval_correct is True

    assert result.passed is True


def test_extract_actual_behavior_for_interrupted_approval() -> None:
    trace = AgentTrace(
        thread_id="test-thread",
    )

    trace.add_event(
        "node_completed",
        node="planner",
        plan=["Delete all saved data."],
        tool_names=["delete_saved_data"],
    )

    trace.add_event(
        "approval_requested",
    )

    behavior = extract_actual_behavior(trace)

    assert behavior.planned_tools == [
        "delete_saved_data",
    ]

    # The protected tool must not execute before approval
    assert behavior.called_tools == []

    assert behavior.approval_required is True
    assert behavior.tool_execution_success is None


def test_evaluate_case_accepts_no_tool_execution_for_no_tool_case() -> None:
    case = EvalCase(
        name="no_tool",
        input="Hello!",
        expected_tools=[],
        expected_approval=False,
    )

    result = evaluate_case(
        case=case,
        actual_tools=[],
        actual_approval=False,
        tool_execution_success=None,
    )

    assert result.tool_selection_correct is True
    assert result.approval_correct is True

    assert result.tool_execution_success is None
    assert result.execution_correct is True

    assert result.passed is True