from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
import logging
import json
from uuid import uuid4
from day03_python_engineering.request_context import request_id_var
from day03_python_engineering.tools.result import ToolErrorCode, ToolResult
from day03_python_engineering.agent.result import AgentRunResult
from langgraph.types import Command

from day03_python_engineering.workflow.langgraph_workflow import (
    create_agent_graph,
)

from langgraph.errors import GraphRecursionError

from day03_python_engineering.exceptions import AgentWorkflowError

logger = logging.getLogger(__name__)

class Agent:
    def __init__(
        self,
        client: OllamaClient,
        registry: ToolRegistry,
        checkpointer,
        tool_groups: set[str] | None = None,
        max_steps: int = 10,
        max_messages: int = 20,
        graph_recursion_limit: int = 30,
        
    ):
        self.client = client
        self.registry = registry
        self.checkpointer = checkpointer
        self.tool_groups = set(tool_groups) if tool_groups is not None else None
        self.max_steps = max_steps
        self.max_messages = max_messages
        self.graph_recursion_limit = graph_recursion_limit
        self.last_thread_id: str | None = None

        self.base_system_prompt = (
            "You are a helpful AI assistant."
        )

        self.messages = [
            {
                "role": "system",
                "content": self.base_system_prompt,
            }
        ]

        # Build the LangGraph workflow
        self.graph = create_agent_graph(
            client=self.client,
            registry=self.registry,
            checkpointer=self.checkpointer,
            tool_groups=self.tool_groups,
        )

        

    async def run(
            self,
            user_input: str,
            session_id: str,
        ) -> AgentRunResult:
        token = None
        if request_id_var.get() is None:
            token = request_id_var.set(uuid4().hex)

        try:
            return await self._run(user_input, session_id)
        finally:
            if token is not None:
                request_id_var.reset(token)

   


    async def _run(
            self, 
            user_message: str,
            session_id: str,       
            ) -> AgentRunResult:
        # Add the new user message to the conversation history
        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # Build the initial state for LangGraph
        initial_state = {
            "original_request": user_message,
            "messages": self.messages,
            "tool_calls": [],
            "plan": [],
            "current_step": 0,
            "step_results": [],

            # No step has been reviewed yet
            "step_success": True,

            # No review feedback exists at startup
            "review_feedback": "",
            "replan_count": 0,

            # No approval decision has been made yet
            "approval": False,
            # No human approval is required by default
            "requires_approval": False,

            "step": 0,
        }

        # Create a unique checkpoint thread for this workflow execution
        thread_id = f"{session_id}:{uuid4()}"
        # Keep the latest workflow thread ID for checkpoint inspection
        self.last_thread_id = thread_id
        # Execute the graph with a recursion limit
        try:
        

            # Execute the graph with a recursion limit
            final_state = await self.graph.ainvoke(
                initial_state,
                config={
                    # Limit the total number of graph node executions
                    "recursion_limit": self.graph_recursion_limit,

                    # Use the application session as the LangGraph checkpoint thread
                    "configurable": {
                        "thread_id": thread_id,
                    },
                },
            )
            # Return workflow information when execution is paused
            interrupts = final_state.get("__interrupt__", [])

            if interrupts:
                return AgentRunResult(
                    status="interrupted",
                    thread_id=thread_id,
                    interrupt=interrupts[0].value,
                )
        except GraphRecursionError as exc:
            raise AgentWorkflowError(
                "Agent workflow exceeded the maximum number of steps."
            ) from exc

       # Get the final answer produced by the workflow
        final_answer = final_state["messages"][-1]["content"]

        # Save only the final assistant answer to the conversation history
        self.messages.append(
            {
                "role": "assistant",
                "content": final_answer,
            }
        )

        # Trim old conversation messages
        self._trim_messages()

        return AgentRunResult(
            status="completed",
            answer=final_answer,
            thread_id=thread_id,
        )

    def _trim_messages(self):
        if len(self.messages) <= self.max_messages + 1:
            return

        system_message = self.messages[0]

        recent_messages = self.messages[-self.max_messages:]

        self.messages = [
            system_message,
            *recent_messages,
        ]

    def set_user_memory(
        self,
        memory_prompt: str,
    ) -> None:
        content = self.messages[0]["content"]
    
        if memory_prompt:
            content += (
                "\n\nLong-term information about the user:\n"
                f"{memory_prompt}\n\n"
                "Use the long-term user information above when the user "
                "asks about themselves. "
                "Do not search the knowledge base for information that is "
                "already available in the user's long-term memory."
            )

        self.messages[0]["content"] = content


    async def get_graph_state(
        self,
        thread_id: str,
    ):
        # Read the latest checkpoint for the workflow execution
        config = {
            "configurable": {
                "thread_id": thread_id,
            },
        }

        return await self.graph.aget_state(config)


    async def resume(
        self,
        thread_id: str,
        decision: bool,
    ) -> AgentRunResult:
        # Reuse the original thread ID to load the saved checkpoint
        config = {
            "recursion_limit": self.graph_recursion_limit,
            "configurable": {
                "thread_id": thread_id,
            },
        }

        # Resume the workflow from the saved interrupt
        final_state = await self.graph.ainvoke(
            Command(resume=decision),
            config=config,
        )

        # Return workflow information if execution is interrupted again
        interrupts = final_state.get("__interrupt__", [])

        if interrupts:
            return AgentRunResult(
                status="interrupted",
                thread_id=thread_id,
                interrupt=interrupts[0].value,
            )
        # Get the final answer after the resumed workflow completes
        final_answer = final_state["messages"][-1]["content"]

        # Save only the final assistant answer to conversation history
        self.messages.append(
            {
                "role": "assistant",
                "content": final_answer,
            }
        )

        # Trim old conversation messages
        self._trim_messages()

        return AgentRunResult(
            status="completed",
            answer=final_answer,
            thread_id=thread_id,
        )