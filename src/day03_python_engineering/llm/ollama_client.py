from asyncio import timeout

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

    async def close(self):
        await self.client.aclose()