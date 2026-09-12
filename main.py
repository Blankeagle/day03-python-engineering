from day03_python_engineering.agent.agent import Agent
from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.tools.time_tool import get_current_time
from day03_python_engineering.tools.weather_tool import get_weather


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

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称",
                    }
                },
                "required": ["city"],
            },
        },
    },
]

agent = Agent(
    client=client,
    registry=registry,
    tools=tools,
    max_steps=10,
    max_messages=20,
)

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    answer = agent.run(user_input)

    print("AI:", answer)