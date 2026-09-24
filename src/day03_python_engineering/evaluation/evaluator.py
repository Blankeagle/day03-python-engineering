from day03_python_engineering.evaluation.models import (
    EvalCase,
    EvalResult,
)


def evaluate_case(
    case: EvalCase,
    actual_tools: list[str],
    actual_approval: bool,
) -> EvalResult:
    # Check whether the agent selected the expected tools
    tools_match = actual_tools == case.expected_tools

    # Check whether the approval decision matches the expectation
    approval_match = actual_approval == case.expected_approval

    # The case passes only when every check succeeds
    passed = tools_match and approval_match

    return EvalResult(
        name=case.name,
        actual_tools=actual_tools,
        actual_approval=actual_approval,
        passed=passed,
    )