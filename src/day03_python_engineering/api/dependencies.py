from day03_python_engineering.agent.agent import Agent
from day03_python_engineering.session.manager import SessionManager
from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.tools.time_tool import get_current_time
from day03_python_engineering.tools.weather_tool import get_weather
from day03_python_engineering.tools.tools import tools


_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    return _session_manager


def create_agent() -> Agent:
    client = OllamaClient()

    registry = ToolRegistry()

    registry.register(
        "get_current_time",
        get_current_time,
    )

    registry.register(
        "get_weather",
        get_weather,
    )

    return Agent(
        client=client,
        registry=registry,
        tools=tools,
        max_steps=10,
        max_messages=20,
    )