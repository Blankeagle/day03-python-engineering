from day03_python_engineering.workflow.nodes import LLMNode, ToolNode
from day03_python_engineering.workflow.state import AgentState


class WorkflowMaxStepsError(Exception):
    """Raised when the workflow exceeds the maximum number of steps."""

class AgentWorkflow:
    def __init__(
        self,
        llm_node: LLMNode,
        tool_node: ToolNode,
        max_steps: int = 10,
    ):
        self.llm_node = llm_node
        self.tool_node = tool_node
        self.max_steps = max_steps

    async def run(self, state: AgentState) -> AgentState:
        # Continue until the workflow finishes or reaches the step limit
        while state.step < self.max_steps:
            # Let the LLM decide whether a tool is required
            state = await self.llm_node.run(state)

            # Finish normally when no tool call is requested
            if not state.tool_calls:
                return state

            # Execute the requested tools
            state = await self.tool_node.run(state)

        # Reaching this point means the workflow did not finish normally
        raise WorkflowMaxStepsError(
            f"Workflow exceeded max_steps={self.max_steps}"
        )