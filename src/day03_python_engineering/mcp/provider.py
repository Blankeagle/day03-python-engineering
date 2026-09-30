from mcp import Client, StdioServerParameters

from day03_python_engineering.mcp.adapter import (
    register_mcp_tools,
)
from day03_python_engineering.tools.registry import (
    ToolRegistry,
)


class MCPToolProvider:
    def __init__(
        self,
        registry: ToolRegistry,
        server: StdioServerParameters,
    ) -> None:
        # Store the application tool registry
        self._registry = registry

        # Store the MCP server configuration
        self._server = server

        # The client is created when the provider starts
        self._client: Client | None = None

    async def __aenter__(self) -> "MCPToolProvider":
        # Create the MCP client
        self._client = Client(
            self._server
        )

        # Open the client connection and start the stdio server
        await self._client.__aenter__()

        try:
            # Discover MCP tools and register them in the application registry
            await register_mcp_tools(
                registry=self._registry,
                client=self._client,
            )
        except Exception:
            # Clean up the client when startup fails
            await self._client.__aexit__(
                None,
                None,
                None,
            )
            self._client = None
            raise

        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if self._client is None:
            return

        # Close the MCP connection and its stdio server process
        await self._client.__aexit__(
            exc_type,
            exc_value,
            traceback,
        )

        self._client = None