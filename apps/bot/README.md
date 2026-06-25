# JobFlow Discord Bot

`apps/bot/` contains the Discord slash-command client. The bot stays intentionally thin: it receives Discord interactions, calls [`apps/api`](../api/), and formats the API response for Discord.

It does not talk directly to Chroma, MongoDB, Redis, or Google GenAI.

## Folder Contents

| Path | Purpose |
| --- | --- |
| `main.py` | Discord client, slash-command registration, and command handlers. |
| `config.py` | Environment-backed bot settings. |
| `api_client.py` | Async HTTP client for the FastAPI backend. |
| `formatters.py` | Discord-safe job and answer formatting plus message splitting. |
| `dev_watch.py` | Local/container file watcher used for bot reloads in development. |
| `Dockerfile` | Bot container image. |
| `docker-compose.bot.yml` | Compose service included by the root compose file. |
| `requirements.txt` | Bot runtime dependencies. |

## Commands

| Command | API endpoint | Purpose |
| --- | --- | --- |
| `/ask question` | `POST /chat` | Ask a natural-language job question and receive a grounded answer with sources. |
| `/jobs query` | `POST /jobs/search` | Search matching jobs without an AI-written explanation. |
| `/reset` | `DELETE /chat/history/{user_id}` | Clear the current Discord user's stored chat history. |

Long responses are split under Discord's message limit by `formatters.py`.

## Running

From the project root:

```bash
make bot-dev
```

Docker:

```bash
docker compose up -d bot
```

The Docker service waits for the API healthcheck before starting.

## Configuration

Use the root [`.env.example`](../../.env.example) as the source of truth. For the bot, the key settings are:

| Variable | Purpose |
| --- | --- |
| `DISCORD_BOT_ENABLED` | Must be `true` for the login loop to start. |
| `DISCORD_TOKEN` | Discord bot token. |
| `DISCORD_GUILD_ID` | Optional guild id for faster command sync during development. |
| `API_BASE_URL` | API base URL. Use `http://api:8100` in Docker and `http://localhost:8100` for local dev. |
| `API_TIMEOUT_SECONDS` | HTTP timeout for API calls. |
