import asyncio
from pathlib import Path

from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.rag.embedding_client import EmbeddingClient
from day03_python_engineering.rag.indexer import DocumentIndexer
from day03_python_engineering.rag.retriever import Retriever
from day03_python_engineering.rag.service import RAGService
from day03_python_engineering.rag.text_splitter import TextSplitter
from src.day03_python_engineering.rag.chroma_store import ChromaVectorStore


async def main():
    embedding_client = EmbeddingClient()
    llm_client = OllamaClient()

    store = ChromaVectorStore(
        path="data/chroma_db",
        collection_name="documents",
    )
    splitter = TextSplitter(
        chunk_size=200,
        chunk_overlap=50,
    )

    indexer = DocumentIndexer(
        embedding_client=embedding_client,
        splitter=splitter,
        store=store,
    )

    retriever = Retriever(
        embedding_client=embedding_client,
        store=store,
    )

    rag_service = RAGService(
        retriever=retriever,
        llm_client=llm_client,
    )

    try:
        await indexer.index_directory(
            Path("data")
        )

        question = (
            "How many vacation days do employees get?"
        )

        result = await rag_service.answer(
            question=question,
            top_k=3,
        )

        print("Question:")
        print(question)

        print("\nAnswer:")
        print(result.answer)

        print("\nSources:")
        for source in result.sources:
            print(
                f"- {source.source} "
                f"(chunk {source.chunk_id})"
            )

    finally:
        await embedding_client.close()
        await llm_client.close()


if __name__ == "__main__":
    asyncio.run(main())