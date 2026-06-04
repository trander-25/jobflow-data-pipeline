# JobFlow Chatbot API

`apps/api/` is the FastAPI backend for the Discord chatbot. It implements the RAG logic:

1. Receive a user question.
2. Retrieve relevant job documents from Chroma.
3. Load recent per-user chat history from MongoDB.
4. Build a grounded prompt.
5. Call Google GenAI.
6. Store the user and assistant messages back to MongoDB.
7. Return the answer, source links, and retrieved job metadata.

## Folder Contents

| Path | Purpose |
| --- | --- |
| `main.py` | FastAPI app, startup wiring, HTTP endpoints. |
| `config.py` | Environment-backed settings for Chroma, MongoDB, GenAI, and RAG limits. |
| `schemas.py` | Pydantic request/response models. |
| `services/chroma_store.py` | Chroma HTTP client, search, and result mapping into `JobSource`. |
| `services/history_store.py` | MongoDB chat-history read/write/delete logic. |
| `services/llm.py` | Google GenAI client wrapper. |
| `services/prompt.py` | Prompt and retrieved-job context builder. |
| `Dockerfile` | Container image for the API service. |
| `docker-compose.api.yml` | Compose service included by the root compose file. |
| `requirements.txt` | Minimal API runtime dependencies. |

## API Endpoints

Base URL in local Docker: `http://localhost:8100`

### `GET /health`

Checks whether the API can reach Chroma and MongoDB.

Response:

```json
{
  "status": "ok",
  "chroma": "ok",
  "mongodb": "ok",
  "timestamp": "2026-06-03T16:00:00Z"
}
```

If one dependency is down, `status` becomes `degraded` and the dependency field becomes `unavailable`.

### `POST /jobs/search`

Searches Chroma and returns matching jobs without calling the LLM.

Request:

```json
{
  "query": "data engineer remote Python"
}
```

The API infers the result size from natural language. For example, `cho tôi 2 job lương cao nhất` returns 2 jobs; broad searches return at most 5 jobs. `top_k` is still accepted as a manual API override.

Response fields:

| Field | Description |
| --- | --- |
| `answer` | Empty string for this endpoint. |
| `sources` | Compact source links with job id, title, company, and URL. |
| `retrieved_jobs` | Full mapped job metadata returned from Chroma. |
| `usage_context` | Retrieval settings such as requested count, retrieval mode, retrieved count, and `llm_used=false`. |

### `POST /chat`

Runs the full chatbot flow: Chroma retrieval, MongoDB history, prompt building, GenAI answer generation, and history persistence.

Request:

```json
{
  "user_id": "discord-user-id",
  "message": "Có job Data Engineer ở TP.HCM không?"
}
```

Response fields:

| Field | Description |
| --- | --- |
| `answer` | Model-generated answer grounded in retrieved jobs. |
| `sources` | Job links used as answer sources. |
| `retrieved_jobs` | Full retrieved jobs for UI/debug display. |
| `usage_context` | Requested count, retrieval mode, retrieved count, history count, model id, and `llm_used=true`. |

If `GOOGLE_API_KEY` is not configured, or if Google GenAI rejects the configured model/request, this endpoint returns a fallback answer with `usage_context.llm_used=false` and `usage_context.llm_error` so Discord users still receive retrieved job sources instead of a bot error.

### `DELETE /chat/history/{user_id}`

Deletes all stored MongoDB chat messages for a user.

Response:

```json
{
  "user_id": "discord-user-id",
  "deleted_messages": 4
}
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `CHROMA_HOST` | `localhost` | Chroma host. Docker uses service name `chroma`. |
| `CHROMA_PORT` | `8000` | Chroma HTTP port. |
| `CHROMA_COLLECTION_NAME` | `job_embeddings` | Collection populated by the Airflow embedding task. |
| `MONGODB_HOST` | `localhost` | MongoDB host. Docker uses service name `mongodb`. |
| `MONGODB_PORT` | `27017` | MongoDB port. |
| `MONGODB_USERNAME` | `user` | MongoDB username. |
| `MONGODB_PASSWORD` | `password` | MongoDB password. |
| `MONGODB_DB` | `jobflow` | Database that contains chatbot messages. |
| `MONGODB_AUTH_SOURCE` | `admin` | MongoDB auth database. |
| `MONGODB_CHAT_COLLECTION` | `chat_messages` | Collection used by the history store. |
| `GOOGLE_API_KEY` | empty | Google AI API key. Required for `/chat`. |
| `GOOGLE_GENAI_MODEL` | `gemini-2.0-flash` | Model id passed to `google-genai`. |
| `GOOGLE_GENAI_TEMPERATURE` | `0.2` | Generation temperature. |
| `CHAT_HISTORY_LIMIT` | `6` | Number of recent messages loaded from MongoDB. |
| `RATE_LIMIT_ENABLED` | `true` | Enables request throttling. |
| `RATE_LIMIT_REQUESTS` | `10` | Maximum requests allowed per rate-limit key. |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Fixed-window size for the request limit. |
| `RATE_LIMIT_SEARCH_ENABLED` | `true` | Applies rate limiting to `/jobs/search` as well as `/chat`. |
| `REDIS_HOST` | `redis` | Redis host used by the rate limiter. |
| `REDIS_PORT` | `6379` | Redis port used by the rate limiter. |
| `REDIS_DB` | `0` | Redis database index used by the rate limiter. |
| `REDIS_SOCKET_TIMEOUT_SECONDS` | `2.0` | Redis connection/read timeout in seconds. |
| `REDIS_RATE_LIMIT_PREFIX` | `jobflow:rate_limit` | Prefix for rate-limit keys stored in Redis. |
| `API_HOST_PORT` | `8100` | Host port used by Docker Compose. |

## Rate Limiting

The API uses Redis-backed fixed-window rate limiting to reduce chatbot spam:

- `/chat` is limited by `user_id`.
- `/jobs/search` is limited by `user_id` when provided, otherwise by client host.
- When the limit is exceeded, the API returns HTTP `429` with a `Retry-After` header.

Default behavior allows `10` requests per `60` seconds per key. Counters are stored in Redis with keys like `jobflow:rate_limit:chat:<user_id>` and `jobflow:rate_limit:jobs:<user_id-or-client-host>`, so multiple API replicas share the same rate-limit state. If Redis is unavailable at startup, the API logs the error and falls back to the in-memory limiter for local resilience.

## Running Locally

From the project root:

```bash
make api-dev
```

This starts:

```bash
PYTHONPATH=apps .venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8100 --reload
```

For useful responses, Chroma must already contain embedded jobs. Run the Airflow embedding DAG after the dbt pipeline has produced the `vector_db` model.

## Docker

The root Compose file includes this service through `apps/api/docker-compose.api.yml`.

```bash
docker compose up -d api
```

The API container waits for healthy `chroma` and `mongodb` services before starting.
In Docker development, `apps/api` is mounted into the container and Uvicorn runs with `--reload`, so Python code changes are picked up after saving without rebuilding the image.
