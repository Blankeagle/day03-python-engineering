import json
import asyncio
from types import SimpleNamespace

import day03_python_engineering.session.redis_store as redis_store_module
from day03_python_engineering.session.redis_store import RedisSessionStore


class FakeRedis:
    def __init__(self):
        self.data: dict[str, str] = {}
        self.url = None
        self.decode_responses = None

    async def set(self, key: str, value: str, ex: int | None = None):
        self.data[key] = value
        self.expiry = ex

    async def get(self, key: str):
        return self.data.get(key)

    async def delete(self, key: str):
        self.data.pop(key, None)

    async def exists(self, key: str):
        return 1 if key in self.data else 0

def test_save_messages_uses_session_key_and_json(monkeypatch):
    fake_client = FakeRedis()

    def fake_from_url(url: str, decode_responses: bool):
        fake_client.url = url
        fake_client.decode_responses = decode_responses
        return fake_client

    monkeypatch.setattr(redis_store_module.redis.Redis, "from_url", fake_from_url)
    monkeypatch.setattr(
        redis_store_module,
        "settings",
        SimpleNamespace(redis_url="redis://localhost:6379/0"),
    )

    messages = [{"role": "user", "content": "你好"}]
    store = RedisSessionStore()
    asyncio.run(store.save_messages("session-1", messages))

    assert fake_client.url == "redis://localhost:6379/0"
    assert fake_client.decode_responses is True
    assert fake_client.expiry == 3600
    assert fake_client.data["session:session-1:messages"] == json.dumps(
        messages,
        ensure_ascii=False,
    )


def test_load_messages_returns_saved_messages(monkeypatch):
    fake_client = FakeRedis()
    fake_client.data["session:session-1:messages"] = json.dumps(
        [{"role": "assistant", "content": "你好"}],
        ensure_ascii=False,
    )

    monkeypatch.setattr(
        redis_store_module.redis.Redis,
        "from_url",
        lambda url, decode_responses: fake_client,
    )
    monkeypatch.setattr(
        redis_store_module,
        "settings",
        SimpleNamespace(redis_url="redis://localhost:6379/0"),
    )

    store = RedisSessionStore()

    assert asyncio.run(store.load_messages("session-1")) == [
        {"role": "assistant", "content": "你好"}
    ]


def test_load_messages_returns_none_for_missing_session(monkeypatch):
    fake_client = FakeRedis()

    monkeypatch.setattr(
        redis_store_module.redis.Redis,
        "from_url",
        lambda url, decode_responses: fake_client,
    )
    monkeypatch.setattr(
        redis_store_module,
        "settings",
        SimpleNamespace(redis_url="redis://localhost:6379/0"),
    )

    store = RedisSessionStore()

    assert asyncio.run(store.load_messages("missing-session")) is None


def test_delete_messages_removes_session_key(monkeypatch):
    fake_client = FakeRedis()

    def fake_from_url(url: str, decode_responses: bool):
        return fake_client

    monkeypatch.setattr(
        redis_store_module.redis.Redis,
        "from_url",
        fake_from_url,
    )

    monkeypatch.setattr(
        redis_store_module,
        "settings",
        SimpleNamespace(
            redis_url="redis://localhost:6379/0",
        ),
    )

    fake_client.data[
        "session:session-1:messages"
    ] = json.dumps(
        [{"role": "user", "content": "你好"}],
        ensure_ascii=False,
    )

    store = RedisSessionStore()

    asyncio.run(store.delete_messages("session-1"))

    assert "session:session-1:messages" not in fake_client.data

def test_exists_returns_true_when_session_exists(monkeypatch):
    fake_client = FakeRedis()

    def fake_from_url(url: str, decode_responses: bool):
        return fake_client

    monkeypatch.setattr(
        redis_store_module.redis.Redis,
        "from_url",
        fake_from_url,
    )

    monkeypatch.setattr(
        redis_store_module,
        "settings",
        SimpleNamespace(
            redis_url="redis://localhost:6379/0",
        ),
    )

    fake_client.data[
        "session:session-1:messages"
    ] = "[]"

    store = RedisSessionStore()

    assert asyncio.run(store.exists("session-1")) is True

def test_exists_returns_false_when_session_missing(monkeypatch):
    fake_client = FakeRedis()

    def fake_from_url(url: str, decode_responses: bool):
        return fake_client

    monkeypatch.setattr(
        redis_store_module.redis.Redis,
        "from_url",
        fake_from_url,
    )

    monkeypatch.setattr(
        redis_store_module,
        "settings",
        SimpleNamespace(
            redis_url="redis://localhost:6379/0",
        ),
    )

    store = RedisSessionStore()

    assert asyncio.run(store.exists("missing-session")) is False

def test_close_closes_redis_client(monkeypatch):
    fake_client = FakeRedis()
    fake_client.closed = False

    async def close():
        fake_client.closed = True

    fake_client.aclose = close
    monkeypatch.setattr(
        redis_store_module.redis.Redis,
        "from_url",
        lambda url, decode_responses: fake_client,
    )

    store = RedisSessionStore()
    asyncio.run(store.close())

    assert fake_client.closed is True
