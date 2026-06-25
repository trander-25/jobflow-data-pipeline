import logging
import time

import discord
from discord import app_commands

from bot.api_client import JobFlowApiClient
from bot.config import get_settings
from bot.formatters import format_chat_response, format_jobs_response, split_discord_message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()
api_client = JobFlowApiClient(settings)


class JobFlowBot(discord.Client):
    """Discord client that owns the JobFlow slash-command tree."""

    def __init__(self) -> None:
        """Initialize a minimal Discord client and command tree."""
        intents = discord.Intents.none()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """Sync slash commands globally or to a configured development guild."""
        if settings.discord_guild_id:
            guild = discord.Object(id=int(settings.discord_guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Synced slash commands to guild %s", settings.discord_guild_id)
        else:
            await self.tree.sync()
            logger.info("Synced global slash commands")


client = JobFlowBot()


async def _send_chunks(interaction: discord.Interaction, message: str) -> None:
    """Send a potentially long response as one or more Discord follow-up messages."""
    chunks = split_discord_message(message)
    await interaction.followup.send(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@client.tree.command(name="ask", description="Ask JobFlow AI about matching jobs")
@app_commands.describe(question="Your job-search question")
async def ask(interaction: discord.Interaction, question: str) -> None:
    """Handle /ask by calling the JobFlow chat API and returning the answer."""
    await interaction.response.defer(thinking=True)
    try:
        payload = await api_client.ask(user_id=str(interaction.user.id), question=question)
        await _send_chunks(interaction, format_chat_response(payload))
    except Exception as exc:
        logger.exception("Failed to handle /ask")
        await interaction.followup.send(f"JobFlow API error: {exc}")


@client.tree.command(name="jobs", description="Search matching jobs in JobFlow")
@app_commands.describe(query="Search query")
async def jobs(interaction: discord.Interaction, query: str) -> None:
    """Handle /jobs by calling semantic search and returning matching jobs."""
    await interaction.response.defer(thinking=True)
    try:
        payload = await api_client.search_jobs(
            query=query,
            user_id=str(interaction.user.id),
        )
        await _send_chunks(interaction, format_jobs_response(payload))
    except Exception as exc:
        logger.exception("Failed to handle /jobs")
        await interaction.followup.send(f"JobFlow API error: {exc}")


@client.tree.command(name="reset", description="Clear your JobFlow chat history")
async def reset(interaction: discord.Interaction) -> None:
    """Handle /reset by clearing the current user's stored chat history."""
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        payload = await api_client.reset_history(user_id=str(interaction.user.id))
        deleted = payload.get("deleted_messages", 0)
        await interaction.followup.send(f"Cleared {deleted} messages from your JobFlow history.", ephemeral=True)
    except Exception as exc:
        logger.exception("Failed to handle /reset")
        await interaction.followup.send(f"JobFlow API error: {exc}", ephemeral=True)


def main() -> None:
    """Start the Discord bot when enabled by environment configuration."""
    if not settings.discord_bot_enabled:
        logger.warning("Discord bot is disabled. Set DISCORD_BOT_ENABLED=true and DISCORD_TOKEN to enable it.")
        while True:
            time.sleep(3600)

    if not settings.discord_token:
        raise ValueError("DISCORD_TOKEN is not configured")
    if settings.discord_token == "your_discord_token":
        raise ValueError("DISCORD_TOKEN still contains the .env.example placeholder value")
    client.run(settings.discord_token)


if __name__ == "__main__":
    main()
