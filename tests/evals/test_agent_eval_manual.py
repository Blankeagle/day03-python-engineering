import pytest
from langgraph.checkpoint.memory import MemorySaver

from day03_python_engineering.api.dependencies import create_agent
from day03_python_engineering.evaluation.evaluator import evaluate_trace

from tests.evals.cases import EVAL_CASES
pytestmark = pytest.mark.manual

@pytest.mark.asyncio
@pytest.mark.eval
@pytest.mark.parametrize(
    "case",
    EVAL_CASES,
    ids=lambda case: case.name,
)
async def test_agent_eval(case) -> None:
    # Use an isolated in-memory checkpoint store for each evaluation case
    checkpointer = MemorySaver()

    # Create a fresh agent so cases do not share conversation state
    agent = create_agent(
        checkpointer=checkpointer,
    )

    # Execute the real agent
    result = await agent.run(
        user_input=case.input,
        session_id=f"eval-{case.name}",
    )

    # Approval cases may intentionally interrupt the workflow
    if case.expected_approval:
        assert result.status == "interrupted"
    else:
        assert result.status == "completed"

    assert agent.last_trace is not None

    # Evaluate the real runtime behavior
    eval_result = evaluate_trace(
        case=case,
        trace=agent.last_trace,
    )

    print(
        f"\nEVAL CASE: {case.name}\n"
        f"RESULT: {eval_result}\n"
    )

    assert eval_result.passed is True