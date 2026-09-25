class OllamaServiceError(Exception):
    pass


class OllamaTimeoutError(Exception):
    pass

class AgentWorkflowError(Exception):
    """Raised when the agent workflow cannot complete normally."""

class InvalidAgentOutputError(Exception):
    """Raised when the agent produces an invalid final output."""