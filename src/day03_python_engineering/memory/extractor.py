import json

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.memory.models import MemoryUpdate


system_prompt = """
Extract long-term user information from the user's message.

Return only valid JSON.

Possible memory fields:
- name
- occupation
- response_preference

Rules:
1. If the user provides new information, put it in the corresponding field.
2. If a field is not mentioned, set it to null.
3. If the user explicitly asks to forget or remove information,
   add that field name to forget_fields.
4. Do not put a field in forget_fields unless the user explicitly
   asks to forget or remove it.

Example:
User: Forget my occupation.

Output:
{
  "name": null,
  "occupation": null,
  "response_preference": null,
  "forget_fields": ["occupation"]
}
"""

class MemoryExtractor:
    def __init__(self, llm_client: OllamaClient):
        self.llm_client = llm_client

    async def extract(
        self,
        message: str,
    ) -> MemoryUpdate:
        messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": message,
        },
    ]
        response = await self.llm_client.chat(
            messages=messages,
        )

        content = response["message"]["content"]

        data = json.loads(content)

        return MemoryUpdate.model_validate(data)