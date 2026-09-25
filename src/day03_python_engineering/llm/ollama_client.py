from asyncio import timeout
import json
import httpx

from day03_python_engineering.config import settings
from day03_python_engineering.exceptions import (
    OllamaServiceError,
    OllamaTimeoutError,
)
http_timeout = httpx.Timeout(
    connect=3.0,
    read=60.0,
    write=10.0,
    pool=5.0,
)


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model_name = settings.model_name
        self.client = httpx.AsyncClient(
            timeout=http_timeout,
        )

    async def chat(
            self,
            messages: list[dict],
            tools: list[dict] | None = None,
            format: str | dict | None = None,
        ):
    
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        if tools is not None:
            payload["tools"] = tools

        # Ask Ollama to return structured JSON when required
        if format:
            payload["format"] = format

        try:
          
            response = await self.client.post(
                url,
                json=payload,
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                "Ollama request timed out"
            ) from e

        except httpx.HTTPError as e:
            raise OllamaServiceError(
                "Ollama service failed"
            ) from e

    async def chat_stream(
        self,
        messages: list[dict],
    ):
        # Build the Ollama chat endpoint
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
        }

        try:
            # Keep the HTTP connection open while Ollama generates the response
            async with self.client.stream(
                "POST",
                url,
                json=payload,
            ) as response:
                response.raise_for_status()

                # Ollama sends one JSON object per line
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Parse one JSON object from the Ollama stream
                    chunk = json.loads(line)

                    # Expose only assistant content, never model thinking
                    content = chunk.get("message", {}).get("content", "")

                    if content:
                        yield content

        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                "Ollama streaming request timed out"
            ) from e

        except httpx.HTTPError as e:
            raise OllamaServiceError(
                "Ollama streaming service failed"
            ) from e

    async def close(self):
        await self.client.aclose()