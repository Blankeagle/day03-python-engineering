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
        # Continue running until the workflow reaches the step limit
        while state.step < self.max_steps:
            # The LLM node decides whether a tool is needed
            state = await self.llm_node.run(state)

            # Finish the workflow if the LLM does not request any tools
            if not state.tool_calls:
                return state 

            # Execute all tools requested by the LLM
            state = await self.tool_node.run(state)

        return state