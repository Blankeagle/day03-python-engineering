from day03_python_engineering.workflow.langgraph_nodes import (
    build_final_context,
)


def test_build_final_context_combines_step_results():
    step_results = [
        "First step result.",
        "Second step result.",
        "Third step result.",
    ]

    context = build_final_context(step_results)

    assert context == (
        "First step result.\n\n"
        "Second step result.\n\n"
        "Third step result."
    )

def test_build_final_context_handles_empty_results():
    context = build_final_context([])

    assert context == ""

def test_build_final_context_keeps_results_within_budget():
    step_results = [
        "AAAA",
        "BBBB",
    ]

    context = build_final_context(
        step_results,
        max_chars=10,
    )

    assert context == "AAAA\n\nBBBB"
    assert len(context) == 10


def test_build_final_context_excludes_result_over_budget():
    step_results = [
        "AAAA",
        "BBBB",
        "CCCC",
    ]

    context = build_final_context(
        step_results,
        max_chars=10,
    )

    assert context == "AAAA\n\nBBBB"
    assert "CCCC" not in context
    assert len(context) <= 10

def test_build_final_context_truncates_single_large_result():
    step_results = [
        "A" * 20,
    ]

    context = build_final_context(
        step_results,
        max_chars=10,
    )

    assert context == "A" * 10
    assert len(context) == 10