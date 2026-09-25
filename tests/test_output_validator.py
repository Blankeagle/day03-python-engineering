import pytest

from day03_python_engineering.exceptions import InvalidAgentOutputError
from day03_python_engineering.guardrails.output_validator import (
    MAX_FINAL_OUTPUT_LENGTH,
    validate_final_output,
)


def test_validate_final_output_accepts_valid_text():
    result = validate_final_output("Hello")

    assert result == "Hello"


@pytest.mark.parametrize(
    "content",
    [
        None,
        "",
        "   ",
        "\n\n",
        123,
        {},
        [],
    ],
)
def test_validate_final_output_rejects_invalid_content(content):
    with pytest.raises(InvalidAgentOutputError):
        validate_final_output(content)




def test_validate_final_output_accepts_maximum_length():
    # The exact maximum length should still be accepted
    content = "a" * MAX_FINAL_OUTPUT_LENGTH

    result = validate_final_output(content)

    assert result == content


def test_validate_final_output_rejects_excessive_length():
    # One character beyond the maximum should be rejected
    content = "a" * (MAX_FINAL_OUTPUT_LENGTH + 1)

    with pytest.raises(
        InvalidAgentOutputError,
        match="exceeds the maximum allowed length",
    ):
        validate_final_output(content)