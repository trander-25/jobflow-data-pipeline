# Apps

`apps/` contains the user-facing services that sit on top of the JobFlow data platform.

| Folder | Purpose |
| --- | --- |
| [`api/`](api/) | FastAPI RAG backend for job search, chat generation, and chat history. |
| [`bot/`](bot/) | Discord slash-command bot that calls the API. |

## Runtime Flow

```text
Discord user
    |
    v
apps/bot
    |
    v
apps/api
    |
    +--> Chroma        job embedding retrieval
    +--> MongoDB       per-user chat history
    +--> Redis         shared API rate limiting
    +--> Google GenAI  answer generation
```

The data used by the apps is prepared by Airflow and dbt:

1. Crawlers collect TopCV and ITViec jobs.
2. dbt builds the `vector_db` model.
3. Airflow embeds new rows into the Chroma collection configured by `CHROMA_COLLECTION_NAME`.
4. The API retrieves those jobs for `/jobs/search` and `/chat`.

## Running

From the project root:

```bash
make run
```

For local app-only development:

```bash
make api-dev
make bot-dev
```

The Makefile runs both services with `PYTHONPATH=apps`, so imports such as `api.main` and `bot.main` resolve from this folder.

## Docker Compose

The root [`docker-compose.yml`](../docker-compose.yml) includes:

| File | Service |
| --- | --- |
| [`api/docker-compose.api.yml`](api/docker-compose.api.yml) | FastAPI backend on host port `API_HOST_PORT` (`8100` by default). |
| [`bot/docker-compose.bot.yml`](bot/docker-compose.bot.yml) | Discord bot, started after the API healthcheck passes. |

## Configuration

Use the root [`.env.example`](../.env.example) as the source of truth. The most important app settings are:

| Variable | Used by |
| --- | --- |
| `API_HOST_PORT`, `API_BASE_URL`, `API_TIMEOUT_SECONDS` | API/bot networking. |
| `GOOGLE_API_KEY`, `GOOGLE_GENAI_MODEL`, `GOOGLE_GENAI_TEMPERATURE` | API answer generation. |
| `CHROMA_*` | Job embedding retrieval. |
| `MONGODB_*` | Chat history storage. |
| `REDIS_*`, `RATE_LIMIT_*` | API rate limiting. |
| `DISCORD_BOT_ENABLED`, `DISCORD_TOKEN`, `DISCORD_GUILD_ID` | Discord bot startup and command sync. |
