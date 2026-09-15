from day03_python_engineering.memory.models import (
    UserMemory,
    MemoryUpdate,
)
from day03_python_engineering.memory.redis_store import RedisMemoryStore
from day03_python_engineering.memory.extractor import MemoryExtractor

import asyncio

class MemoryService:
    def __init__(
        self,
        store: RedisMemoryStore,
        extractor: MemoryExtractor,
    ):
        self.store = store
        self.extractor = extractor
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(
        self,
        user_id: str,
    ) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()

        return self._locks[user_id]

    
    async def get_memory(
        self,
        user_id: str,
    ) -> UserMemory:
        memory = await self.store.load(user_id)

        if memory is None:
            return UserMemory(user_id=user_id)

        return memory

    async def save_memory(
        self,
        memory: UserMemory,
    ) -> None:
        await self.store.save(memory)

    async def update_memory(
        self,
        user_id: str,
        update: MemoryUpdate,
    ) -> UserMemory:
        memory = await self.get_memory(user_id)

        update_data = update.model_dump(
            exclude_none=True,
            exclude={"forget_fields"},
        )

        for field_name in update.forget_fields:
            if field_name in UserMemory.model_fields:
                update_data[field_name] = None

        updated_memory = memory.model_copy(
            update=update_data
        )

        await self.store.save(updated_memory)

        return updated_memory

    async def process_message(
        self,
        user_id: str,
        message: str,
    ) -> UserMemory:
        # If the message does not contain any keywords that 
        # indicate the user is providing information about themselves, 
        # we skip the extraction process and return the existing memory. 
        # for less token usage and faster response time.
        if not self.should_extract(message):
            return await self.get_memory(user_id)

        update = await self.extractor.extract(message)

        return await self.update_memory(
            user_id=user_id,
            update=update,
        )

    # This method checks if the message contains any keywords that 
    # indicate the user is providing information about themselves, 
    # which should be extracted and stored in long-term memory.
    # incase the message contains any of these keywords, it returns True,
    def should_extract(self, message: str) -> bool:
        keywords = [
            # add / update memory
            "my name",
            "i am",
            "i'm",
            "i work",
            "i prefer",

            # forget memory
            "forget",
            "remove",
            "don't remember",
            "do not remember",
        ]

        text = message.lower()

        return any(
            keyword in text
            for keyword in keywords
        )

    import asyncio


