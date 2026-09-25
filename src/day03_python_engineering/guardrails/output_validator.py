from day03_python_engineering.exceptions import InvalidAgentOutputError


MAX_FINAL_OUTPUT_LENGTH = 20_000


def validate_final_output(content: object) -> str:
    # Require the final agent output to be non-empty text
    if not isinstance(content, str) or not content.strip():
        raise InvalidAgentOutputError(
            "The agent produced an invalid final answer."
        )

    # Reject unexpectedly large final outputs
    if len(content) > MAX_FINAL_OUTPUT_LENGTH:
        raise InvalidAgentOutputError(
            "The agent final answer exceeds the maximum allowed length."
        )

    return content