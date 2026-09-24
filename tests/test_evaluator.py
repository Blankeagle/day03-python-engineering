from day03_python_engineering.evaluation.evaluator import evaluate_case
from day03_python_engineering.evaluation.models import EvalCase


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
    )

    assert result.name == "current_time"
    assert result.actual_tools == ["get_current_time"]
    assert result.actual_approval is False
    assert result.passed is True


def test_evaluate_case_fails_when_tool_does_not_match() -> None:
    # Define the expected agent behavior
    case = EvalCase(
        name="current_time",
        input="What time is it now?",
        expected_tools=["get_current_time"],
        expected_approval=False,
    )

    # Evaluate behavior with the wrong tool
    result = evaluate_case(
        case=case,
        actual_tools=["get_weather"],
        actual_approval=False,
    )

    assert result.passed is False