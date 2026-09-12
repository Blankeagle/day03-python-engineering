import asyncio

from day03_python_engineering.agent.agent import Agent
from day03_python_engineering.session.redis_store import RedisSessionStore


class SessionManager:
    def __init__(self, store: RedisSessionStore):
        self._agents: dict[str, Agent] = {}
        self._store = store
        self._locks: dict[str, asyncio.Lock] = {}

    def lock(self, session_id: str) -> asyncio.Lock:
        return self._locks.setdefault(session_id, asyncio.Lock())

    def get(self, session_id: str) -> Agent | None:
        return self._agents.get(session_id)

    async def set(self, session_id: str, agent: Agent):
        self._agents[session_id] = agent

        await self._store.save_messages(
            session_id=session_id,
            messages=agent.messages,
        )

    async def load_messages(
        self,
        session_id: str,
    ) -> list[dict] | None:
        return await self._store.load_messages(session_id)

    async def delete(self, session_id: str):

        await self._store.delete_messages(session_id)
        self._agents.pop(session_id, None)


    async def exists(self, session_id: str) -> bool:
        return await self._store.exists(session_id)