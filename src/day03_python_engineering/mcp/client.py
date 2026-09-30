import anyio

from mcp import StdioServerParameters

from day03_python_engineering.mcp.provider import (
    MCPToolProvider,
)
from day03_python_engineering.tools.registry import (
    ToolRegistry,
)


async def main() -> None:
    registry = ToolRegistry()

    server = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "day03_python_engineering.mcp.server",
        ],
    )

    async with MCPToolProvider(
        registry=registry,
        server=server,
    ):
        print("REGISTERED TOOLS:")
        print(registry.list_tools())

        result = await registry.execute(
            name="get_server_time",
            arguments={},
        )

        print("TOOL RESULT:")
        print(result)


if __name__ == "__main__":
    anyio.run(main)