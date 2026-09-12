from day03_python_engineering.agent.agent import Agent


class SessionManager:
    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def get(self, session_id: str) -> Agent | None:
        return self._agents.get(session_id)

    def set(self, session_id: str, agent: Agent):
        self._agents[session_id] = agent

    def delete(self, session_id: str):
        self._agents.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        return session_id in self._agents