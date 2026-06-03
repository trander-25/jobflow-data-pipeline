import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = _int_env("CHROMA_PORT", 8000)
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "job_embeddings")

    mongodb_host: str = os.getenv("MONGODB_HOST", "localhost")
    mongodb_port: int = _int_env("MONGODB_PORT", 27017)
    mongodb_username: str = os.getenv("MONGODB_USERNAME", "user")
    mongodb_password: str = os.getenv("MONGODB_PASSWORD", "password")
    mongodb_db: str = os.getenv("MONGODB_DB", "jobflow")
    mongodb_auth_source: str = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    mongodb_chat_collection: str = os.getenv("MONGODB_CHAT_COLLECTION", "chat_messages")

    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_genai_model: str = os.getenv("GOOGLE_GENAI_MODEL", "gemma-3-27b-it")
    google_genai_temperature: float = _float_env("GOOGLE_GENAI_TEMPERATURE", 0.2)

    rag_default_top_k: int = _int_env("RAG_DEFAULT_TOP_K", 5)
    rag_max_top_k: int = _int_env("RAG_MAX_TOP_K", 10)
    chat_history_limit: int = _int_env("CHAT_HISTORY_LIMIT", 6)
    rate_limit_enabled: bool = _bool_env("RATE_LIMIT_ENABLED", True)
    rate_limit_requests: int = _int_env("RATE_LIMIT_REQUESTS", 10)
    rate_limit_window_seconds: int = _int_env("RATE_LIMIT_WINDOW_SECONDS", 60)
    rate_limit_search_enabled: bool = _bool_env("RATE_LIMIT_SEARCH_ENABLED", True)

    @property
    def mongodb_uri(self) -> str:
        username = self.mongodb_username
        password = self.mongodb_password
        host = self.mongodb_host
        port = self.mongodb_port
        auth_source = self.mongodb_auth_source
        return f"mongodb://{username}:{password}@{host}:{port}/{self.mongodb_db}?authSource={auth_source}"


def get_settings() -> Settings:
    return Settings()
