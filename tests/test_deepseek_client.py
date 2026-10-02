import json
from copy import deepcopy

import httpx
import pytest

from day03_python_engineering.llm.deepseek_client import DeepSeekClient
from day03_python_engineering.exceptions import OllamaServiceError, OllamaTimeoutError
from day03_python_engineering.workflow.langgraph_nodes import create_tool_node
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.tools.time_tool import CurrentTimeInput
from day03_python_engineering.observability.trace import AgentTrace


@pytest.fixture
def client():
    return DeepSeekClient("test-key", "https://example.test/v1/")


async def mock_transport(client, handler):
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_tool_round_trip(client):
    requests = []
    def handler(request):
        requests.append(json.loads(request.content))
        assert request.headers["Authorization"] == "Bearer test-key"
        assert str(request.url) == "https://example.test/v1/chat/completions"
        if len(requests) == 1:
            message = {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function",
                 "function": {"name": "clock", "arguments": "{}"}}
            ]}
        else:
            message = {"role": "assistant", "content": "12:00"}
        return httpx.Response(200, json={"choices": [{"message": message}]})
    await mock_transport(client, handler)
    registry = ToolRegistry()
    registry.register("clock", "clock", lambda: "12:00", CurrentTimeInput)
    messages = [{"role": "user", "content": "time?"}]
    try:
        response = await client.chat(messages, tools=registry.get_tool_schemas())
        message = response["message"]
        assert message["content"] == ""
        assert message["tool_calls"][0]["function"]["arguments"] == {}
        state = {
            "messages": [*messages, message], "tool_calls": message["tool_calls"],
            "approval": False, "trace": AgentTrace(thread_id="test"), "step": 0,
        }
        update = await create_tool_node(registry)(state)
        original = deepcopy(update["messages"])
        result = await client.chat(update["messages"])
        assert result["message"]["content"] == "12:00"
        assert requests[1]["messages"][-1]["tool_call_id"] == "call_1"
        assert requests[1]["messages"][-2]["tool_calls"][0]["function"]["arguments"] == "{}"
        assert update["messages"] == original
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("format", ["json", {"type": "object", "properties": {"success": {"type": "boolean"}}}])
async def test_json_mode(client, format):
    messages = [{"role": "user", "content": "review"}]
    def handler(request):
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        assert "JSON" in payload["messages"][0]["content"]
        if isinstance(format, dict):
            assert json.dumps(format) in payload["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": '{"success":true}'}}]})
    await mock_transport(client, handler)
    try:
        assert json.loads((await client.chat(messages, format=format))["message"]["content"])["success"]
        assert messages == [{"role": "user", "content": "review"}]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_stream_content_only(client):
    def handler(request):
        assert json.loads(request.content)["stream"] is True
        chunks = [
            {"choices": [{"delta": {"reasoning_content": "private"}}]},
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": []},
            {"choices": [{"delta": {"content": " world"}}]},
        ]
        body = ": keepalive\n\n" + "".join("data: " + json.dumps(c) + "\n\n" for c in chunks)
        body += "data: [DONE]\n\ndata: invalid\n\n"
        return httpx.Response(200, text=body, headers={"Content-Type": "text/event-stream"})
    await mock_transport(client, handler)
    try:
        assert [t async for t in client.chat_stream([])] == ["Hello", " world"]
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("failure", ["timeout", "http", "invalid"])
async def test_errors(client, stream, failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        if failure == "http":
            return httpx.Response(503)
        return httpx.Response(200, text="data: invalid\n\n" if stream else "{}")
    await mock_transport(client, handler)
    error = OllamaTimeoutError if failure == "timeout" else OllamaServiceError
    try:
        with pytest.raises(error):
            if stream:
                [t async for t in client.chat_stream([])]
            else:
                await client.chat([])
    finally:
        await client.close()
