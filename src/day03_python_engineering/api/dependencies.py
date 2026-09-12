from day03_python_engineering.agent.agent import Agent
from day03_python_engineering.session.manager import SessionManager
from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.tools.time_tool import get_current_time
from day03_python_engineering.tools.weather_tool import get_weather
from day03_python_engineering.tools.tools import tools
from day03_python_engineering.session.redis_store import RedisSessionStore


_redis_store = RedisSessionStore()

_session_manager = SessionManager(
    store=_redis_store,
)

def get_session_manager() -> SessionManager:
    return _session_manager


_ollama_client = OllamaClient()

_tool_registry = ToolRegistry()
_tool_registry.register(
    "get_current_time",
    get_current_time,
)
_tool_registry.register(
    "get_weather",
    get_weather,
)


def create_agent() -> Agent:
 

    return Agent(
        client=_ollama_client,
        registry=_tool_registry,
        tools=tools,
        max_steps=10,
        max_messages=20,
    )

async def close_dependencies():
    await _ollama_client.close()
    await _redis_store.close()
