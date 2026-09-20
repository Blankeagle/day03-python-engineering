from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
import logging
import json
from uuid import uuid4

from day03_python_engineering.request_context import request_id_var
from day03_python_engineering.tools.result import ToolErrorCode, ToolResult

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
        tool_groups: set[str] | None = None,
        max_steps: int = 10,
        max_messages: int = 20,
        graph_recursion_limit: int = 30,
    ):
        self.client = client
        self.registry = registry
        self.tool_groups = set(tool_groups) if tool_groups is not None else None
        self.max_steps = max_steps
        self.max_messages = max_messages
        self.graph_recursion_limit = graph_recursion_limit

        self.base_system_prompt = (
            "You are a helpful AI assistant."
        )

        self.messages = [
            {
                "role": "system",
                "content": self.base_system_prompt,
            }
        ]

        # # Create the LLM execution node
        # self.llm_node = LLMNode(
        #     client=self.client,
        #     registry=self.registry,
        #     tool_groups=self.tool_groups,
        # )

        # # Create the tool execution node
        # self.tool_node = ToolNode(
        #     registry=self.registry,
        #     tool_groups=self.tool_groups,
        # )

        # # Build the workflow that controls node execution
        # self.workflow = AgentWorkflow(
        #     llm_node=self.llm_node,
        #     tool_node=self.tool_node,
        #     max_steps=self.max_steps,
        # )

        # Build the LangGraph workflow
        self.graph = create_agent_graph(
            client=self.client,
            registry=self.registry,
            tool_groups=self.tool_groups,
        )

        

    async def run(self, user_input: str) -> str:
        token = None
        if request_id_var.get() is None:
            token = request_id_var.set(uuid4().hex)

        try:
            return await self._run(user_input)
        finally:
            if token is not None:
                request_id_var.reset(token)

    # async def _run(self, user_input: str) -> str:
    #     self.messages.append(
    #         {
    #             "role": "user",
    #             "content": user_input,
    #         }
    #     )
    #     self._trim_messages()

    #     for step in range(self.max_steps):
    #         response = await self.client.chat(
    #             messages=self.messages,
    #             tools=self.registry.get_tool_schemas(groups=self.tool_groups),
    #             )

    #         message = response["message"]

    #         self.messages.append(message)

    #         tool_calls = message.get("tool_calls", [])

    #         if not tool_calls:
    #             return message["content"]

    #         for tool_call in tool_calls:
    #             tool_name = tool_call["function"]["name"]

    #             arguments = tool_call["function"].get(
    #                 "arguments",
    #                 {},
    #             )

    #             try:
    #                 result = await self.registry.execute(
    #                     tool_name,
    #                     arguments,
    #                     groups=self.tool_groups,
    #                 )

    #             except Exception:
    #                 logger.exception("tool %s failed outside registry", tool_name)
    #                 result = ToolResult(
    #                     success=False,
    #                     error=ToolErrorCode.TOOL_EXECUTION_ERROR,
    #                     message="Tool execution failed.",
    #                 )

    #             logger.info(
    #                 "agent step=%s tool=%s arguments=%s result=%s",
    #                 step + 1,
    #                 tool_name,
    #                 arguments,
    #                 result,
    #             )

    #             self.messages.append(
    #                 {
    #                     "role": "tool",
    #                     "name": tool_name,
    #                     "content": result.model_dump_json()
    #                 }
    #             )

    #     return "Agent 超过最大执行步数，任务未完成。"


    async def _run(self, user_message: str) -> str:
        # Add the new user message to the conversation history
        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # Build the initial state for LangGraph
        initial_state = {
            # Start with the current conversation history
            "messages": self.messages,
            "tool_calls": [],
            "plan": [],
            "current_step": 0,

            # Store completed plan step results
            "step_results": [],

            "step": 0,
        }
        # Execute the graph with a recursion limit
        try:
            # Execute the graph with a recursion limit
            final_state = await self.graph.ainvoke(
            initial_state,
            config={
                # Limit the total number of graph node executions
                "recursion_limit": self.graph_recursion_limit,
            },
        )
        except GraphRecursionError as exc:
            raise AgentWorkflowError(
                "Agent workflow exceeded the maximum number of steps."
            ) from exc

        # Save the conversation history returned by the graph
        self.messages = final_state["messages"]

        # Trim old conversation messages
        self._trim_messages()

        # Return the final assistant response
        return self.messages[-1]["content"]

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


    async def debug_stream(
        self,
        user_message: str,
    ) -> None:
        # Build an isolated message list for debugging
        messages = [
            *self.messages,
            {
                "role": "user",
                "content": user_message,
            },
        ]

        # Build the initial graph state
        initial_state = {
            "messages": self.messages,
            "tool_calls": [],
            "plan": [],
            "current_step": 0,

            # Store completed plan step results
            "step_results": [],

            "step": 0,
        }

        # Stream graph updates node by node
        async for event in self.graph.astream(
            initial_state,
            config={
                "recursion_limit": self.graph_recursion_limit,
            },
            stream_mode="updates",
        ):
            print("GRAPH EVENT:", event)