import pytest
from langgraph.checkpoint.memory import MemorySaver

from day03_python_engineering.api.dependencies import create_agent
from day03_python_engineering.evaluation.evaluator import (
    evaluate_trace,
    summarize_results,
)
from day03_python_engineering.evaluation.models import EvalResult

from tests.evals.cases import EVAL_CASES


@pytest.mark.asyncio
@pytest.mark.eval
async def test_agent_eval_summary() -> None:
    # Collect evaluation results from all real agent runs
    eval_results: list[EvalResult] = []

    for case in EVAL_CASES:
        # Create an isolated agent for each evaluation case
        checkpointer = MemorySaver()

        agent = create_agent(
            checkpointer=checkpointer,
        )

        # Execute the real agent workflow
        run_result = await agent.run(
            user_input=case.input,
            session_id=f"eval-{case.name}",
        )

        # Verify the expected workflow stopping behavior
        if case.expected_approval:
            assert run_result.status == "interrupted"
        else:
            assert run_result.status == "completed"

        assert agent.last_trace is not None

        # Evaluate the actual runtime behavior
        eval_result = evaluate_trace(
            case=case,
            trace=agent.last_trace,
        )

        eval_results.append(eval_result)

        print(
            f"\nCASE: {case.name}\n"
            f"RESULT: {eval_result}\n"
        )

    # Aggregate all evaluation results
    summary = summarize_results(
        eval_results
    )

    print("\n=== AGENT EVALUATION SUMMARY ===")
    print(f"Total Cases: {summary.total_cases}")

    print(
        "Tool Selection: "
        f"{summary.tool_selection_correct}/{summary.total_cases} "
        f"({summary.tool_selection_accuracy:.2%})"
    )

    print(
        "Execution: "
        f"{summary.execution_correct}/{summary.total_cases} "
        f"({summary.execution_accuracy:.2%})"
    )

    print(
        "Approval: "
        f"{summary.approval_correct}/{summary.total_cases} "
        f"({summary.approval_accuracy:.2%})"
    )

    print(
        "Overall: "
        f"{summary.passed_cases}/{summary.total_cases} "
        f"({summary.pass_rate:.2%})"
    )

    # The initial evaluation dataset should pass all expected behaviors
    assert summary.pass_rate == pytest.approx(1.0)