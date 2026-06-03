# Apps

`apps/` contains user-facing application services that sit on top of the data platform in `infra/`.

The current applications are:

| Folder | Purpose |
| --- | --- |
| [`api/`](./api/) | FastAPI RAG backend that searches Chroma, calls Google GenAI, and stores chat history in MongoDB. |
| [`bot/`](./bot/) | Discord slash-command bot that calls the FastAPI backend for chat and job search. |

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
    +--> Chroma      job embedding search
    +--> MongoDB     per-user chat history
    +--> Google GenAI answer generation
```

The data used by these apps is prepared by the Airflow/dbt embedding pipeline:

1. Crawlers collect jobs from TopCV and ITViec.
2. dbt builds the `vector_db` model.
3. Airflow embeds new rows into the Chroma collection configured by `CHROMA_COLLECTION_NAME`.
4. `apps/api` retrieves those embedded jobs for chatbot answers.

## Local Development

From the project root:

```bash
make api-dev
make bot-dev
```

The Makefile runs both services with `PYTHONPATH=apps`, so imports such as `api.main` and `bot.main` resolve from this folder.

## Docker Compose

The root [`docker-compose.yml`](../docker-compose.yml) includes:

- [`apps/api/docker-compose.api.yml`](./api/docker-compose.api.yml)
- [`apps/bot/docker-compose.bot.yml`](./bot/docker-compose.bot.yml)

The API service depends on healthy Chroma and MongoDB. The bot service depends on the API healthcheck.

## Environment Variables

The app-level variables are defined in [`.env.example`](../.env.example). The most important ones are:

| Variable | Used by | Description |
| --- | --- | --- |
| `API_HOST_PORT` | API Docker service | Host port exposed for FastAPI. Defaults to `8100`. |
| `API_BASE_URL` | Discord bot | Base URL used by the bot to call the API. In Docker it should be `http://api:8100`. |
| `GOOGLE_API_KEY` | API | Google AI API key used by `google-genai`. Required for `/chat`. |
| `GOOGLE_GENAI_MODEL` | API | Model id used for answer generation. Defaults to `gemini-2.0-flash`. |
| `RATE_LIMIT_ENABLED` | API | Enables per-user API rate limiting. |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | API | Maximum requests allowed per key inside the configured time window. |
| `RATE_LIMIT_SEARCH_ENABLED` | API | Applies the same limiter to `/jobs/search`. |
| `DISCORD_BOT_ENABLED` | Bot | Keeps the bot disabled by default until a real Discord token is configured. |
| `DISCORD_TOKEN` | Bot | Discord bot token. Required to start the bot. |
| `DISCORD_GUILD_ID` | Bot | Optional guild id for faster slash-command sync during development. |
