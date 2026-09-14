import asyncio

import httpx

from day03_python_engineering.config import settings


class EmbeddingClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=3.0,
                read=30.0,
                write=10.0,
                pool=5.0,
            )
        )
        self._semaphore = asyncio.Semaphore(
            settings.embedding_max_concurrency
        )     

    async def embed(self, text: str) -> list[float]:
        response = await self.client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text,
            },
        )
  
        response.raise_for_status()

        data = response.json()

        return data["embedding"]

    async def close(self):
        await self.client.aclose()

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return await asyncio.gather(
            *(
                self._embed_with_limit(text)
                for text in texts
            )
        )
    
    async def _embed_with_limit(
        self,
        text: str,
    ) -> list[float]:
        async with self._semaphore:
            return await self.embed(text)
