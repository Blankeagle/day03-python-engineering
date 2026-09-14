import pytest
from pydantic import BaseModel

from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.tools.result import ToolErrorCode


class AddInput(BaseModel):
    a: int
    b: int


def add(a: int, b: int) -> int:
    return a + b


@pytest.mark.asyncio
async def test_execute_sync_tool():
    registry = ToolRegistry()

    registry.register(
        name="add",
        description="Add two numbers",
        func=add,
        input_model=AddInput,
    )

    result = await registry.execute(
        name="add",
        arguments={
            "a": 1,
            "b": 2,
        },
    )

    assert result.success is True
    assert result.data == 3

@pytest.mark.asyncio
async def test_invalid_arguments():
    registry = ToolRegistry()

    registry.register(
        name="add",
        description="Add two numbers",
        func=add,
        input_model=AddInput,
    )

    result = await registry.execute(
        name="add",
        arguments={
            "a": 1,
            "b": "hello",
        },
    )

    assert result.success is False
    assert result.error.value ==ToolErrorCode.INVALID_ARGUMENTS

@pytest.mark.asyncio
async def test_tool_not_found():
    registry = ToolRegistry()

    result = await registry.execute(
        name="not_exists",
        arguments={},
    )

    assert result.success is False
    assert result.error.value == ToolErrorCode.TOOL_NOT_FOUND

class MultiplyInput(BaseModel):
    a: int
    b: int


async def multiply(a: int, b: int) -> int:
    return a * b   

@pytest.mark.asyncio
async def test_execute_async_tool():
    registry = ToolRegistry()

    registry.register(
        name="multiply",
        description="Multiply two numbers",
        func=multiply,
        input_model=MultiplyInput,
    )

    result = await registry.execute(
        name="multiply",
        arguments={
            "a": 3,
            "b": 4,
        },
    )

    assert result.success is True
    assert result.data == 12