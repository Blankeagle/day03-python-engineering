import httpx

from day03_python_engineering.exceptions import (
    OllamaServiceError,
    OllamaTimeoutError,
)


class DeepSeekClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str = "deepseek-chat",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

        self.client = httpx.AsyncClient(
            timeout=60.0,
        )

    async def chat(
        self,
        messages: list[dict],
        format: str | None = None,
    ) -> str:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }
        if format == "json":
            payload["response_format"] = {
                "type": "json_object"
            }

        try:
            response = await self.client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                "DeepSeek request timed out"
            ) from e

        except httpx.HTTPError as e:
            raise OllamaServiceError(
                "DeepSeek service failed"
            ) from e

    async def close(self) -> None:
        await self.client.aclose()