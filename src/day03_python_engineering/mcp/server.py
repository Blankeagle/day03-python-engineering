from datetime import datetime, timezone

from mcp.server import MCPServer


# Create the MCP server
mcp = MCPServer("day03-agent")


@mcp.tool()
def get_server_time() -> str:
    """Return the current UTC server time."""
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    mcp.run()