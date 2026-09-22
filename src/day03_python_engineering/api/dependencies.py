from functools import partial

import httpx

from day03_python_engineering.rag.embedding_client import EmbeddingClient
from day03_python_engineering.rag.chroma_store import ChromaVectorStore
from day03_python_engineering.rag.retriever import Retriever
from day03_python_engineering.rag.service import RAGService

from day03_python_engineering.agent.agent import Agent
from day03_python_engineering.config import settings
from day03_python_engineering.session.manager import SessionManager
from day03_python_engineering.llm.ollama_client import OllamaClient
from day03_python_engineering.tools.registry import ToolRegistry
from day03_python_engineering.session.redis_store import RedisSessionStore
from day03_python_engineering.tools.weather_tool import (
    get_weather,
    WeatherInput,
)
from day03_python_engineering.tools.time_tool import (
    get_current_time,
    CurrentTimeInput,
)

from pathlib import Path

from day03_python_engineering.rag.indexer import DocumentIndexer
from day03_python_engineering.rag.text_splitter import TextSplitter
from src.day03_python_engineering.tools.rag_tool import RAGQueryInput, search_knowledge_base

from day03_python_engineering.memory.redis_store import RedisMemoryStore
from day03_python_engineering.memory.extractor import MemoryExtractor
from day03_python_engineering.memory.service import MemoryService




_redis_store = RedisSessionStore()

_session_manager = SessionManager(
    store=_redis_store,
)

# The shared LangGraph checkpointer is initialized during application startup
_checkpointer = None


def get_session_manager() -> SessionManager:
    return _session_manager


_ollama_client = OllamaClient()
_weather_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=3.0,
        read=10.0,
        write=10.0,
        pool=5.0,
    )
)
_tool_registry = ToolRegistry(timeout_seconds=settings.tool_timeout_seconds)
_tool_registry.register(
    "get_current_time",
    "获取当前时间",
    get_current_time,
    input_model=CurrentTimeInput,
)

_embedding_client = EmbeddingClient()

_vector_store = ChromaVectorStore(
    path="data/chroma_db",
    collection_name="documents",
)

_retriever = Retriever(
    embedding_client=_embedding_client,
    store=_vector_store,
)

_rag_service = RAGService(
    retriever=_retriever,
    llm_client=_ollama_client,
)


def get_rag_service() -> RAGService:
    return _rag_service


_tool_registry.register(
    "get_weather",
    "获取指定城市天气",
    partial(get_weather, client=_weather_client),
    input_model=WeatherInput,
    allow_retry=True,
)

_rag_tool = partial(
    search_knowledge_base,
    rag_service=_rag_service,
)
_tool_registry.register(
    name="search_knowledge_base",
    description=(
        "Search the internal knowledge base and answer questions "
        "using the indexed documents."
    ),
    func=_rag_tool,
    input_model=RAGQueryInput,
    allow_retry=False,
    groups={"general", "rag"},
)



_text_splitter = TextSplitter(
    chunk_size=200,
    chunk_overlap=50,
)

_indexer = DocumentIndexer(
    embedding_client=_embedding_client,
    splitter=_text_splitter,
    store=_vector_store,
)


_memory_store = RedisMemoryStore()

_memory_extractor = MemoryExtractor(
    llm_client=_ollama_client,
)

_memory_service = MemoryService(
    store=_memory_store,
    extractor=_memory_extractor,
)


def get_memory_service() -> MemoryService:
    return _memory_service

async def initialize_rag():
    await _indexer.index_directory(
        Path("data")
    )

def create_agent( checkpointer,tool_groups: set[str] | None = None) -> Agent:
 

    return Agent(
        client=_ollama_client,
        registry=_tool_registry,
        checkpointer=checkpointer,
        tool_groups=tool_groups,
        max_steps=10,
        max_messages=20,
    )

async def close_dependencies():
    await _embedding_client.close()
    await _ollama_client.close()
    await _weather_client.aclose()
    await _redis_store.close()
    await _memory_store.close()

def set_checkpointer(checkpointer) -> None:
    global _checkpointer
    _checkpointer = checkpointer


def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("LangGraph checkpointer is not initialized")

    return _checkpointer
