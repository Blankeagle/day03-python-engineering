from pathlib import Path
from typing import Any
from day03_python_engineering.rag.embedding_client import EmbeddingClient
from day03_python_engineering.rag.text_splitter import TextSplitter
from day03_python_engineering.rag.vector_store import InMemoryVectorStore
from day03_python_engineering.rag.store import VectorStore

class DocumentIndexer:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        splitter: TextSplitter,
        store: VectorStore,
    ):
        self.embedding_client = embedding_client
        self.splitter = splitter
        self.store = store

    async def index_file(self, file_path: Path):
        self.store.delete_by_source(file_path.name)

        document = file_path.read_text(
            encoding="utf-8"
        )

        chunks = self.splitter.split(document)

        vectors = await self.embedding_client.embed_many(
            chunks
        )

        for chunk_id, (chunk, vector) in enumerate(
            zip(chunks, vectors)
        ):
            document_id = f"{file_path.name}:{chunk_id}"

            self.store.add(
                document_id=document_id,
                text=chunk,
                vector=vector,
                metadata={
                    "source": file_path.name,
                    "chunk_id": chunk_id,
                },
            )        
            self.store.delete_by_source(file_path.name)

            document = file_path.read_text(
                encoding="utf-8"
            )

            chunks = self.splitter.split(document)
            vectors = await self.embedding_client.embed_many(chunks)
            for chunk_id, (chunk, vector) in enumerate(
                zip(chunks, vectors)
            ):
                document_id = f"{file_path.name}:{chunk_id}"

                self.store.add(
                    document_id=document_id,
                    text=chunk,
                    vector=vector,
                    metadata={
                        "source": file_path.name,
                        "chunk_id": chunk_id,
                    },
                )

    async def index_directory(
        self,
        directory: Path,
    ):
        for file_path in directory.glob("*.txt"):
            await self.index_file(file_path)