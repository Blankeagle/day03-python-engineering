import asyncio

from day03_python_engineering.session.manager import SessionManager


class FakeStore:
    def __init__(self):
        self.messages = {
            "session-1": [
                {
                    "role": "user",
                    "content": "我叫 Jack",
                },
                {
                    "role": "assistant",
                    "content": "你好 Jack",
                },
            ]
        }

    async def load_messages(self, session_id: str):
        return self.messages.get(session_id)

    async def delete_messages(self, session_id: str):
        self.deleted_session_id = session_id
def test_delete_removes_redis_and_memory():
    store = FakeStore()
    manager = SessionManager(store=store)

    manager._agents["session-1"] = object()

    asyncio.run(manager.delete("session-1"))

    assert store.deleted_session_id == "session-1"
    assert "session-1" not in manager._agents

def test_load_messages_from_store():
    store = FakeStore()
    manager = SessionManager(store=store)

    result = asyncio.run(manager.load_messages("session-1"))

    assert result == [
        {
            "role": "user",
            "content": "我叫 Jack",
        },
        {
            "role": "assistant",
            "content": "你好 Jack",
        },
    ]

def test_same_session_lock_serializes_work():
    manager = SessionManager(store=FakeStore())
    events = []

    async def worker(name: str):
        async with manager.lock("session-1"):
            events.append(f"{name}-start")
            await asyncio.sleep(0)
            events.append(f"{name}-end")

    async def run():
        await asyncio.gather(worker("a"), worker("b"))

    asyncio.run(run())
    assert events == ["a-start", "a-end", "b-start", "b-end"]
