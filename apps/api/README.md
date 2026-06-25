# JobFlow Chatbot API

`apps/api/` is the FastAPI backend used by the Discord bot and by direct API clients. It retrieves embedded job records from Chroma, optionally calls Google GenAI, and stores per-user chat history in MongoDB.

## Folder Contents

| Path | Purpose |
| --- | --- |
| `main.py` | FastAPI app, startup wiring, dependency health checks, and HTTP endpoints. |
| `config.py` | Environment-backed settings. |
| `schemas.py` | Pydantic request and response models. |
| `services/chroma_store.py` | Chroma client, result mapping, and source-link building. |
| `services/history_store.py` | MongoDB chat-history read/write/delete logic. |
| `services/llm.py` | Google GenAI wrapper. |
| `services/prompt.py` | Prompt and retrieved-job context builder. |
| `services/query_planner.py` | Query count detection and high-salary sorting helpers. |
| `services/rate_limiter.py` | Redis-backed fixed-window limiter with in-memory fallback. |
| `Dockerfile` | API container image. |
| `docker-compose.api.yml` | Compose service included by the root compose file. |
| `requirements.txt` | API runtime dependencies. |

## Endpoints

Base URL in local Docker: `http://localhost:8100`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Report API, Chroma, and MongoDB status. |
| `POST` | `/jobs/search` | Search Chroma and return matching jobs without the LLM. |
| `POST` | `/chat` | Retrieve jobs, load recent history, call Google GenAI, save messages, and return a grounded answer. |
| `DELETE` | `/chat/history/{user_id}` | Delete all stored chat messages for one user. |

Example search request:

```json
{
  "query": "data engineer remote Python"
}
```

Example chat request:

```json
{
  "user_id": "discord-user-id",
  "message": "Co job Data Engineer o TP.HCM khong?"
}
```

The API can infer a requested result count from the message text. Broad searches return up to 5 jobs unless `top_k` is provided.

## RAG Flow

```text
Request
    |
    +--> query planner
    +--> Chroma retrieval
    +--> MongoDB recent history
    +--> prompt builder
    +--> Google GenAI
    +--> MongoDB append messages
    v
Response with answer, sources, retrieved_jobs, usage_context
```

If `GOOGLE_API_KEY` is missing or the LLM call fails, `/chat` still returns retrieved job sources with `usage_context.llm_used=false`.

## Running

From the project root:

```bash
make api-dev
```

Docker:

```bash
docker compose up -d api
```

For useful answers, Chroma should already contain embedded jobs from the Airflow `embed_vector_db_pipeline` flow.

## Configuration

Use the root [`.env.example`](../../.env.example) as the source of truth. This service mainly depends on `CHROMA_*`, `MONGODB_*`, `REDIS_*`, `RATE_LIMIT_*`, `GOOGLE_*`, `CHAT_HISTORY_LIMIT`, and `API_HOST_PORT`.
