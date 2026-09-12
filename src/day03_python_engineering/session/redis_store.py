import json
import redis.asyncio as redis
from day03_python_engineering.config import settings


class RedisSessionStore:
    def __init__(self):
        self.client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    def _message_key(self, session_id: str) -> str:
        return f"session:{session_id}:messages"

    async def save_messages(self, session_id: str, messages: list[dict]):
        key = self._message_key(session_id)

        await self.client.set(
            key,
            json.dumps(messages, ensure_ascii=False),
            ex=settings.redis_session_ttl_seconds,
        )

    async def load_messages(self, session_id: str) -> list[dict] | None:
        key = self._message_key(session_id)

        data = await self.client.get(key)

        if data is None:
            return None

        return json.loads(data)

    async def delete_messages(self, session_id: str):
        key = self._message_key(session_id)

        await self.client.delete(key)

    async def exists(self, session_id: str) -> bool:
        key = self._message_key(session_id)

        return bool(await self.client.exists(key))

    async def close(self) -> None:
        await self.client.aclose()