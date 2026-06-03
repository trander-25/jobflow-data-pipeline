# Infrastructure

`infra/` contains Docker Compose fragments, bootstrap scripts, and runtime configuration for the local JobFlow data platform.

The root [`docker-compose.yml`](../docker-compose.yml) includes the Compose files from this folder and starts the full local stack.

## Folder Map

| Folder | Purpose |
| --- | --- |
| [`airflow/`](./airflow/) | Airflow image, DAGs, tasks, crawlers, dbt project, and orchestration code. |
| `postgresql/` | PostgreSQL Compose service and SQL initialization scripts for job data, Airflow metadata, and Iceberg catalog metadata. |
| `minio/` | MinIO object storage service used by crawlers and warehouse storage. |
| `trino/` | Trino query engine configuration, catalogs, and schema initialization. |
| `chroma/` | Chroma vector database service used by the chatbot RAG backend. |
| `mongodb/` | MongoDB service and `chat_messages` collection bootstrap for chatbot history. |
| `redis/` | Redis service for cache or queue-oriented extensions. |

## Platform Flow

```text
TopCV / ITViec
    |
    v
Airflow crawlers
    |
    +--> PostgreSQL staging tables
    +--> MinIO object storage
    |
    v
dbt via Trino + Iceberg
    |
    +--> analytics/report models
    +--> vector_db model
    |
    v
Chroma embeddings
    |
    v
apps/api + apps/bot
```

## Compose Files

| File | Service(s) |
| --- | --- |
| `airflow/docker-compose.airflow.yml` | Airflow init, webserver, scheduler. |
| `postgresql/docker-compose.postgresql.yml` | PostgreSQL database. |
| `minio/docker-compose.minio.yml` | MinIO server and bucket initialization. |
| `trino/docker-compose.trino.yml` | Trino server and schema initialization. |
| `chroma/docker-compose.chroma.yml` | Chroma vector database. |
| `mongodb/docker-compose.mongodb.yml` | MongoDB with chat collection initialization. |
| `redis/docker-compose.redis.yml` | Redis. |

## Main Environment Variables

| Variable | Used by | Description |
| --- | --- | --- |
| `DB_USER`, `DB_PASSWORD` | PostgreSQL, Airflow, dbt | Shared local database credentials. |
| `DB_JOB` | PostgreSQL, dbt, crawlers | Job application database. |
| `DB_AIRFLOW` | PostgreSQL, Airflow | Airflow metadata database. |
| `DB_TRINO` | PostgreSQL, Trino/Iceberg | Iceberg JDBC catalog metadata database. |
| `POSTGRES_HOST_PORT` | PostgreSQL | Host port for PostgreSQL. |
| `MINIO_USER`, `MINIO_PASSWORD` | MinIO, Airflow | MinIO root credentials. |
| `MINIO_WAREHOUSE_BUCKET` | MinIO, Trino/Iceberg | Bucket for warehouse data. |
| `MINIO_CRAWLED_DATA_BUCKET` | MinIO, crawlers | Bucket for crawled raw/object data. |
| `TRINO_HOST_PORT` | Trino | Host port for Trino HTTP. |
| `TRINO_CONN_ID` | Airflow | Airflow connection id used by embedding tasks. |
| `CHROMA_HOST`, `CHROMA_PORT` | Airflow, API | Chroma service host and port. |
| `CHROMA_COLLECTION_NAME` | Airflow, API | Collection used for job embeddings. |
| `MONGODB_*` | MongoDB, API | MongoDB service, credentials, and chat database. |
| `REDIS_*` | Redis | Redis image and port settings. |
| `*_VOLUME_NAME` | Docker | Stable volume names for persistent local data. |

See [`.env.example`](../.env.example) for the complete list.

## Running

From the project root:

```bash
make run
```

Useful service-level commands:

```bash
docker compose ps
docker compose logs -f airflow-scheduler
docker compose logs -f chroma
docker compose logs -f api
```

## Data Persistence

Persistent services use named Docker volumes. The Makefile creates these volumes before starting Compose:

- PostgreSQL
- MinIO
- Chroma
- MongoDB

Changing database names or bootstrap schemas after volumes already exist may require resetting the matching volume.
