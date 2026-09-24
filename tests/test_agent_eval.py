import pytest

from day03_python_engineering.evaluation.cases import EVAL_CASES
from day03_python_engineering.evaluation.runner import run_eval_case
from day03_python_engineering.api.dependencies import (
    create_agent,
)
from langgraph.checkpoint.memory import MemorySaver

pytestmark = pytest.mark.eval


@pytest.mark.asyncio
async def test_current_time_agent_eval() -> None:
    # Select the current-time evaluation case
    case = EVAL_CASES[0]

    # Use an in-memory checkpointer for isolated evaluation runs
    checkpointer = MemorySaver()

    # Reuse the production Agent configuration with a test checkpointer
    agent = create_agent(
        checkpointer=checkpointer,
    )

    # Run the real agent evaluation
    result = await run_eval_case(
        agent=agent,
        case=case,
    )

    # Verify that the real agent behavior matches the evaluation case
    assert result.actual_tools == ["get_current_time"]
    assert result.actual_approval is False
    assert result.passed is True


@pytest.mark.asyncio
async def test_knowledge_base_agent_eval() -> None:
    # Select the knowledge-base evaluation case
    case = EVAL_CASES[1]

    # Use an in-memory checkpointer for this evaluation run
    checkpointer = MemorySaver()

    # Reuse the production Agent configuration
    agent = create_agent(
        checkpointer=checkpointer,
    )

    # Run the real agent evaluation
    result = await run_eval_case(
        agent=agent,
        case=case,
    )

    # Verify that the agent selected the RAG tool
    assert result.actual_tools == ["search_knowledge_base"]
    assert result.actual_approval is False
    assert result.passed is True

@pytest.mark.asyncio
async def test_delete_saved_data_requires_approval() -> None:
    # Select the destructive-operation evaluation case
    case = EVAL_CASES[2]

    # Use an in-memory checkpointer for this evaluation run
    checkpointer = MemorySaver()

    # Reuse the production Agent configuration
    agent = create_agent(
        checkpointer=checkpointer,
    )

    # Run the agent until the workflow requests approval
    result = await run_eval_case(
        agent=agent,
        case=case,
    )

    # Verify that the destructive tool was selected
    assert result.actual_tools == ["delete_saved_data"]

    # Verify that human approval was requested
    assert result.actual_approval is True

    # Verify that the behavior matches the evaluation case
    assert result.passed is True