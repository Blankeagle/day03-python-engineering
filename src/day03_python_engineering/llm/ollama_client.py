import httpx

from day03_python_engineering.config import settings


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model_name = settings.model_name

    def chat(self, messages, tools=None):
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        if tools is not None:
            payload["tools"] = tools

        response = httpx.post(
            url,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()