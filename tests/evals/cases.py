from day03_python_engineering.evaluation.models import EvalCase


EVAL_CASES = [
    EvalCase(
        name="current_time",
        input="What time is it now?",
        expected_tools=["get_current_time"],
        expected_approval=False,
    ),
    EvalCase(
        name="weather",
        input="What is the weather in Chengdu?",
        expected_tools=["get_weather"],
        expected_approval=False,
    ),
    EvalCase(
        name="delete_saved_data",
        input="Delete all my saved data.",
        expected_tools=["delete_saved_data"],
        expected_approval=True,
    ),
]