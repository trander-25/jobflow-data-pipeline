import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    """Read an integer environment variable with a default fallback."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    """Read a float environment variable with a default fallback."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _bool_env(name: str, default: bool) -> bool:
    """Read a boolean environment variable using common truthy strings."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the JobFlow API service."""

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
    google_genai_model: str = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")
    google_genai_temperature: float = _float_env("GOOGLE_GENAI_TEMPERATURE", 0.2)

    chat_history_limit: int = _int_env("CHAT_HISTORY_LIMIT", 6)
    rate_limit_enabled: bool = _bool_env("RATE_LIMIT_ENABLED", True)
    rate_limit_requests: int = _int_env("RATE_LIMIT_REQUESTS", 10)
    rate_limit_window_seconds: int = _int_env("RATE_LIMIT_WINDOW_SECONDS", 60)
    rate_limit_search_enabled: bool = _bool_env("RATE_LIMIT_SEARCH_ENABLED", True)

    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = _int_env("REDIS_PORT", 6379)
    redis_db: int = _int_env("REDIS_DB", 0)
    redis_socket_timeout_seconds: float = _float_env("REDIS_SOCKET_TIMEOUT_SECONDS", 2.0)
    redis_rate_limit_prefix: str = os.getenv("REDIS_RATE_LIMIT_PREFIX", "jobflow:rate_limit")

    @property
    def mongodb_uri(self) -> str:
        """Build the MongoDB connection URI from individual settings."""
        username = self.mongodb_username
        password = self.mongodb_password
        host = self.mongodb_host
        port = self.mongodb_port
        auth_source = self.mongodb_auth_source
        return f"mongodb://{username}:{password}@{host}:{port}/{self.mongodb_db}?authSource={auth_source}"


def get_settings() -> Settings:
    """Create a Settings instance from the current process environment."""
    return Settings()
