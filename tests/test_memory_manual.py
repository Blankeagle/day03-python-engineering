import asyncio

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.memory.extractor import MemoryExtractor
from day03_python_engineering.memory.redis_store import RedisMemoryStore
from day03_python_engineering.memory.service import MemoryService


async def main():
    llm_client = OllamaClient()
    store = RedisMemoryStore()

    extractor = MemoryExtractor(
        llm_client=llm_client,
    )

    service = MemoryService(
        store=store,
        extractor=extractor,
    )

    memory = await service.process_message(
        user_id="user-123",
        message="My name is Jack and I am a backend engineer.",
    )

    print(memory)

    await store.close()
    await llm_client.close()


asyncio.run(main())