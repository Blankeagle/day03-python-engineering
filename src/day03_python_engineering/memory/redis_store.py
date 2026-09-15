import json

import redis.asyncio as redis

from day03_python_engineering.config import settings
from day03_python_engineering.memory.models import UserMemory


class RedisMemoryStore:
    def __init__(self):
        self.client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    def _key(self, user_id: str) -> str:
        return f"user:{user_id}:memory"

    async def save(
        self,
        memory: UserMemory,
    ) -> None:
        await self.client.set(
            self._key(memory.user_id),
            memory.model_dump_json(),
        )

    async def load(
        self,
        user_id: str,
    ) -> UserMemory | None:
        data = await self.client.get(
            self._key(user_id)
        )

        if data is None:
            return None

        return UserMemory.model_validate_json(data)

    async def delete(
        self,
        user_id: str,
    ) -> None:
        await self.client.delete(
            self._key(user_id)
        )

    async def close(self) -> None:
        await self.client.aclose()