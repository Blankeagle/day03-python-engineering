from uuid import uuid4
from day03_python_engineering.evaluation.evaluator import evaluate_case
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
    result = await agent.run(
        user_input=case.input,
        session_id=session_id,
    )

        # Read the trace produced by this agent run
    trace = agent.last_trace

    actual_tools: list[str] = []

    if trace is not None:
        # Find the planner completion event
        for event in trace.events:
            if (
                event["event"] == "node_completed"
                and event.get("node") == "planner"
            ):
                actual_tools = event.get("tool_names", [])
                break

                # Check whether this workflow requested human approval
    actual_approval = False

    if trace is not None:
        actual_approval = any(
            event["event"] == "approval_requested"
            for event in trace.events
        )

    # Compare the actual agent behavior with the expected behavior
    return evaluate_case(
        case=case,
        actual_tools=actual_tools,
        actual_approval=actual_approval,
    )