# JobFlow Discord Bot

`apps/bot/` contains the Discord slash-command bot. It is intentionally thin: command handlers collect user input, call the FastAPI backend, and format responses for Discord.

The bot does not talk directly to Chroma, MongoDB, or Google GenAI. Those responsibilities belong to [`apps/api`](../api/).

## Folder Contents

| Path | Purpose |
| --- | --- |
| `main.py` | Discord client, slash-command registration, and command handlers. |
| `config.py` | Environment-backed bot settings. |
| `api_client.py` | Async HTTP client for `apps/api`. |
| `formatters.py` | Discord-safe response formatting and message splitting. |
| `Dockerfile` | Container image for the bot service. |
| `docker-compose.bot.yml` | Compose service included by the root compose file. |
| `requirements.txt` | Minimal bot runtime dependencies. |

## Slash Commands

### `/ask question`

Calls `POST /chat` on the FastAPI backend.

Use this for natural-language questions such as:

```text
/ask Có job backend Python remote lương trên 30 triệu không?
```

Behavior:

- Uses the Discord user id as `user_id`.
- Lets the API retrieve relevant jobs from Chroma.
- Lets the API use MongoDB per-user chat history.
- Returns the generated answer and compact source links.

### `/jobs query`

Calls `POST /jobs/search` on the FastAPI backend.

Use this when the user wants search results without an AI-generated explanation:

```text
/jobs data engineer Ho Chi Minh
```

Behavior:

- Sends `query` and `JOBS_DEFAULT_TOP_K` to the API.
- Formats returned jobs with title, company, location, salary, and URL.

### `/reset`

Calls `DELETE /chat/history/{discord_user_id}` on the FastAPI backend.

Behavior:

- Deletes the current Discord user's stored chat history.
- Replies ephemerally with the number of deleted messages.

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `DISCORD_BOT_ENABLED` | `false` | Enables the Discord login loop. Keep false until a real token is configured. |
| `DISCORD_TOKEN` | empty | Discord bot token. Required to start the bot. |
| `DISCORD_GUILD_ID` | empty | Optional guild id. When set, slash commands sync to that guild for faster development. |
| `API_BASE_URL` | `http://localhost:8100` | FastAPI base URL. Docker default is `http://api:8100`. |
| `API_TIMEOUT_SECONDS` | `45` | HTTP timeout for API calls. |
| `JOBS_DEFAULT_TOP_K` | `5` | Number of jobs requested by `/jobs`. |

## Running Locally

From the project root:

```bash
make bot-dev
```

This runs:

```bash
PYTHONPATH=apps .venv/bin/python -m bot.main
```

For local development, set:

```bash
DISCORD_BOT_ENABLED="true"
DISCORD_TOKEN="your_discord_token"
DISCORD_GUILD_ID="your_test_guild_id"
API_BASE_URL="http://localhost:8100"
```

`DISCORD_GUILD_ID` is optional, but recommended while developing because guild command sync is much faster than global command sync.

## Docker

The root Compose file includes this service through `apps/bot/docker-compose.bot.yml`.

```bash
docker compose up -d bot
```

The bot waits for the `api` service healthcheck before starting.

## Discord Message Formatting

Discord messages have a 2000-character limit. `formatters.py` uses a safe limit of 1900 characters and splits long API responses across multiple follow-up messages.
