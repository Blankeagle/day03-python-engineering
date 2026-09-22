from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    debug: bool
    ollama_base_url: str
    model_name: str
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl_seconds: int = 3600
    tool_timeout_seconds: float = 10.0
    embedding_max_concurrency: int = 5
    langgraph_redis_url: str = "redis://localhost:6380"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()