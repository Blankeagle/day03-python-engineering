from day03_python_engineering.workflow.plan import (
    PlanStep,
    StepStatus,
)
from dataclasses import replace




def test_plan_step_has_pending_default_state() -> None:
    step = PlanStep(
        id="step_1",
        description="Get the current weather.",
    )

    assert step.id == "step_1"
    assert step.description == "Get the current weather."

    assert step.status == StepStatus.PENDING
    assert step.tool_names == []
    assert step.result is None
    assert step.error is None


def test_plan_step_can_store_execution_result() -> None:
    step = PlanStep(
        id="step_1",
        description="Get the current weather.",
        status=StepStatus.COMPLETED,
        tool_names=["get_weather"],
        result="The weather is sunny.",
    )

    assert step.status == StepStatus.COMPLETED
    assert step.tool_names == ["get_weather"]
    assert step.result == "The weather is sunny."
    assert step.error is None


def test_plan_step_can_store_failure() -> None:
    step = PlanStep(
        id="step_1",
        description="Get the current weather.",
        status=StepStatus.FAILED,
        tool_names=["get_weather"],
        error="Weather service unavailable.",
    )

    assert step.status == StepStatus.FAILED
    assert step.result is None
    assert step.error == "Weather service unavailable."



def test_plan_step_success_lifecycle() -> None:
    # Create a new pending step
    pending_step = PlanStep(
        id="step_1",
        description="Get the current time.",
        tool_names=["get_current_time"],
    )

    assert pending_step.status == StepStatus.PENDING

    # Start executing the step
    running_step = replace(
        pending_step,
        status=StepStatus.RUNNING,
    )

    assert running_step.status == StepStatus.RUNNING

    # Complete the step successfully
    completed_step = replace(
        running_step,
        status=StepStatus.COMPLETED,
        result="The current time is 14:30.",
        error=None,
    )

    assert completed_step.status == StepStatus.COMPLETED
    assert completed_step.result == "The current time is 14:30."
    assert completed_step.error is None

    # Copy-on-write should preserve the previous states
    assert pending_step.status == StepStatus.PENDING
    assert running_step.status == StepStatus.RUNNING


def test_plan_step_failure_lifecycle() -> None:
    # Create a new pending step
    pending_step = PlanStep(
        id="step_1",
        description="Get the current weather.",
        tool_names=["get_weather"],
    )

    # Start executing the step
    running_step = replace(
        pending_step,
        status=StepStatus.RUNNING,
    )

    # Mark the step as failed
    failed_step = replace(
        running_step,
        status=StepStatus.FAILED,
        result=None,
        error="Weather tool execution failed.",
    )

    assert failed_step.status == StepStatus.FAILED
    assert failed_step.result is None
    assert failed_step.error == "Weather tool execution failed."

    # Copy-on-write should preserve the previous states
    assert pending_step.status == StepStatus.PENDING
    assert running_step.status == StepStatus.RUNNING