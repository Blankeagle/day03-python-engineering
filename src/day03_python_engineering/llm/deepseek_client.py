import json
from copy import deepcopy

import httpx

from day03_python_engineering.exceptions import OllamaServiceError, OllamaTimeoutError


class DeepSeekClient:
    """Adapt DeepSeek Chat Completions to the agent's existing contract."""

    def __init__(self, api_key: str, base_url: str, model_name: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.client = httpx.AsyncClient(timeout=60.0)

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _payload(self, messages, *, stream, tools=None, format=None):
        wire_messages = deepcopy(messages)
        for message in wire_messages:
            for call in message.get("tool_calls") or []:
                arguments = call["function"].get("arguments", {})
                if not isinstance(arguments, str):
                    call["function"]["arguments"] = json.dumps(arguments)
        payload = {"model": self.model_name, "messages": wire_messages, "stream": stream}
        if tools:
            payload["tools"] = tools
        if format is not None:
            if format != "json" and not isinstance(format, dict):
                raise ValueError("DeepSeek format must be 'json' or a JSON schema")
            instruction = "Return only a valid JSON object."
            if isinstance(format, dict):
                instruction += " Follow this JSON schema: " + json.dumps(format)
            # JSON mode ensures syntax; workflow Pydantic models validate schema.
            wire_messages.insert(0, {"role": "system", "content": instruction})
            payload["response_format"] = {"type": "json_object"}
        return payload

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None,
        format: str | dict | None = None,
    ) -> dict:
        payload = self._payload(messages, stream=False, tools=tools, format=format)
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions", headers=self._headers, json=payload,
            )
            response.raise_for_status()
            message = deepcopy(response.json()["choices"][0]["message"])
            message["content"] = message.get("content") or ""
            for call in message.get("tool_calls") or []:
                arguments = call["function"]["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object")
                call["function"]["arguments"] = arguments
            return {"message": message}
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError("DeepSeek request timed out") from exc
        except httpx.HTTPError as exc:
            raise OllamaServiceError("DeepSeek service failed") from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise OllamaServiceError("DeepSeek returned an invalid response") from exc

    async def chat_stream(self, messages: list[dict]):
        payload = self._payload(messages, stream=True)
        try:
            async with self.client.stream(
                "POST", f"{self.base_url}/chat/completions",
                headers=self._headers, json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    if not data:
                        continue
                    chunk = json.loads(data)
                    if "error" in chunk:
                        raise OllamaServiceError("DeepSeek streaming service failed")
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    content = choices[0].get("delta", {}).get("content")
                    if content:
                        if not isinstance(content, str):
                            raise ValueError("Stream content must be a string")
                        yield content
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError("DeepSeek streaming request timed out") from exc
        except httpx.HTTPError as exc:
            raise OllamaServiceError("DeepSeek streaming service failed") from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise OllamaServiceError("DeepSeek returned an invalid stream") from exc

    async def close(self) -> None:
        await self.client.aclose()
