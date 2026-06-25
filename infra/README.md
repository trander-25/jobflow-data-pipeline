# Infrastructure

`infra/` contains Docker Compose fragments, bootstrap scripts, and runtime configuration for the local JobFlow platform.

The root [`docker-compose.yml`](../docker-compose.yml) includes the Compose files from this folder.

## Folder Map

| Folder | Purpose |
| --- | --- |
| [`airflow/`](airflow/) | Airflow image, DAGs, task helpers, crawlers, validation code, and dbt project. |
| `postgresql/` | PostgreSQL service plus SQL init scripts for job data, Airflow metadata, and Iceberg catalog metadata. |
| `minio/` | MinIO object storage and bucket initialization. |
| `trino/` | Trino server config, Iceberg catalog config, and warehouse schema initialization. |
| `superset/` | Superset BI service, Trino driver bootstrap, and default datasource import. |
| `chroma/` | Chroma vector database used by Airflow embeddings and the API. |
| `mongodb/` | MongoDB service and chat collection bootstrap. |
| `redis/` | Redis service used by the API rate limiter. |

## Platform Flow

```text
Airflow
    |
    +--> PostgreSQL      job tables, Airflow metadata, Iceberg JDBC catalog
    +--> MinIO           warehouse and crawled object buckets
    +--> Trino/Iceberg   SQL lakehouse query layer
    +--> dbt             bronze/silver/gold/report/vector models
    +--> Chroma          embedded jobs for RAG
    +--> Discord         optional job alert posting

Superset reads report tables through Trino.
apps/api reads Chroma, MongoDB, and Redis.
apps/bot calls apps/api.
```

## Compose Files

| File | Service(s) |
| --- | --- |
| `airflow/docker-compose.airflow.yml` | Airflow init, webserver, and scheduler. |
| `postgresql/docker-compose.postgresql.yml` | PostgreSQL. |
| `minio/docker-compose.minio.yml` | MinIO server and bucket init. |
| `trino/docker-compose.trino.yml` | Trino server and schema init. |
| `superset/docker-compose.superset.yml` | Superset init, Trino driver install, datasource import, and web UI. |
| `chroma/docker-compose.chroma.yml` | Chroma vector database. |
| `mongodb/docker-compose.mongodb.yml` | MongoDB and chat collection init. |
| `redis/docker-compose.redis.yml` | Redis. |

## Running

From the project root:

```bash
make run
```

Useful checks:

```bash
make docker-ps
make docker-logs
docker compose logs -f airflow-scheduler
docker compose logs -f trino
docker compose logs -f superset
```

## Configuration

Use the root [`.env.example`](../.env.example) as the source of truth. Defaults are designed for local Docker development.

The important groups are `DB_*`, `MINIO_*`, `TRINO_*`, `SUPERSET_*`, `CHROMA_*`, `MONGODB_*`, `REDIS_*`, `AIRFLOW_*`, and Docker volume names.

## Persistence

Stateful services use named Docker volumes for PostgreSQL, MinIO, Chroma, MongoDB, and Superset home data. If you change database names or bootstrap schema settings after volumes already exist, reset the matching volume before starting again.
