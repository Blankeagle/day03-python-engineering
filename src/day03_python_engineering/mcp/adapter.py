from typing import Any

from mcp import Client
from pydantic import BaseModel, create_model

from day03_python_engineering.tools.registry import ToolRegistry


def schema_to_pydantic_model(
    model_name: str,
    schema: dict,
) -> type[BaseModel]:
    # Map supported JSON Schema types to Python types
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
    }

    properties = schema.get(
        "properties",
        {},
    )

    required_fields = set(
        schema.get("required", [])
    )

    fields: dict[str, Any] = {}

    for field_name, field_schema in properties.items():
        json_type = field_schema.get("type")

        python_type = type_mapping.get(
            json_type,
            Any,
        )

        if field_name in required_fields:
            # Required fields have no default value
            fields[field_name] = (
                python_type,
                ...,
            )
        else:
            # Optional fields use the schema default when available
            default = field_schema.get(
                "default",
                None,
            )

            fields[field_name] = (
                python_type | None,
                default,
            )

    # Create a Pydantic model dynamically at runtime
    return create_model(
        model_name,
        **fields,
    )


async def register_mcp_tools(
    registry: ToolRegistry,
    client: Client,
) -> None:
    # Discover all tools exposed by the MCP server
    tools_result = await client.list_tools()

    for mcp_tool in tools_result.tools:
        # Convert the MCP JSON Schema into a Pydantic input model
        input_model = schema_to_pydantic_model(
            model_name=f"{mcp_tool.name}Input",
            schema=mcp_tool.input_schema,
        )

        # Create an async adapter for this MCP tool
        async def call_tool(
            _tool_name: str = mcp_tool.name,
            **arguments,
        ):
            # Forward the validated arguments to the MCP server
            result = await client.call_tool(
                _tool_name,
                arguments,
            )

            if result.is_error:
                raise RuntimeError(
                    f"MCP tool execution failed: {_tool_name}"
                )

            # Prefer structured MCP output
            if result.structured_content is not None:
                if "result" in result.structured_content:
                    return result.structured_content["result"]

                return result.structured_content

            # Fall back to text content
            if result.content:
                first_content = result.content[0]

                if hasattr(first_content, "text"):
                    return first_content.text

            raise RuntimeError(
                f"MCP tool returned no usable result: {_tool_name}"
            )

        # Register the MCP tool as a normal application tool
        registry.register(
            name=mcp_tool.name,
            description=mcp_tool.description or "",
            func=call_tool,
            input_model=input_model,
        )