import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool) -> bool:
    """Read a boolean environment variable using common truthy strings."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class BotSettings:
    """Runtime configuration for the Discord bot service."""

    discord_bot_enabled: bool = _bool_env("DISCORD_BOT_ENABLED", False)
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8100")
    api_timeout_seconds: float = float(os.getenv("API_TIMEOUT_SECONDS", "120"))


def get_settings() -> BotSettings:
    """Create BotSettings from the current process environment."""
    return BotSettings()
