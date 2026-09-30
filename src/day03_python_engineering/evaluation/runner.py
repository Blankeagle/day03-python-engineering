from uuid import uuid4
from day03_python_engineering.evaluation.evaluator import evaluate_case,evaluate_trace
from day03_python_engineering.agent.agent import Agent
from day03_python_engineering.evaluation.models import (
    EvalCase,
    EvalResult,
)

async def run_eval_case(
    agent: Agent,
    case: EvalCase,
) -> EvalResult:
    # Use an isolated session for this evaluation case
    session_id = f"eval:{case.name}:{uuid4().hex}"

    # Run the evaluation input through the real agent
    await agent.run(
        user_input=case.input,
        session_id=session_id,
    )

    # Read the trace produced by this agent run
    trace = agent.last_trace

    if trace is None:
        raise RuntimeError(
            "Agent did not produce a trace."
        )

    # Evaluate the complete runtime behavior from the trace
    return evaluate_trace(
        case=case,
        trace=trace,
    )