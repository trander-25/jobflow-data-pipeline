# Airflow Runtime

`infra/airflow/` contains the orchestration layer for JobFlow. It builds the Airflow image, defines DAGs and task groups, runs crawlers, executes dbt models, posts job alerts, and embeds jobs into Chroma.

## Folder Contents

| Path | Purpose |
| --- | --- |
| `dags/` | Airflow DAG definitions. |
| `tasks/` | Reusable Python task and task-group helpers used by DAGs. |
| `scripts/` | Crawlers, validation helpers, formatting utilities, storage/database clients, and source config JSON. |
| `dbt_jobflow/` | dbt project with bronze, silver, gold, reports, audit, and vector_db models. |
| `config/airflow.cfg` | Airflow configuration mounted into the containers. |
| `Dockerfile` | Airflow runtime image with Python dependencies and Chrome for Selenium crawlers. |
| `docker-compose.airflow.yml` | Airflow init, webserver, and scheduler services. |
| `requirements.txt` | Python dependencies installed into the Airflow image. |

## Important DAGs

| DAG | Purpose |
| --- | --- |
| `master_dag.py` | End-to-end orchestration that ties crawl, transform, and embedding stages together. |
| `topcv_jobs.py` | TopCV crawl pipeline. |
| `itviec_jobs.py` | ITViec crawl pipeline. |
| `dbt_pipeline.py` | dbt transformation pipeline. |
| `embed_vector_db.py` | Builds the `vector_db` model and embeds records into Chroma. |
| `post_job_dag.py` | Posts unposted job alerts to Discord channels. |
| `process_image_dag.py` | Processes company logo/image assets. |

## dbt Models

The dbt project lives at `dbt_jobflow/`.

| Layer | Path | Description |
| --- | --- | --- |
| Bronze | `models/bronze` | Source-aligned staging models for crawled data. |
| Silver | `models/silver` | Cleaned and unified intermediate job models. |
| Gold | `models/gold` | Fact and dimension models for analytics. |
| Reports | `models/reports` | Business-ready report models. |
| Audit | `models/audit` | Pipeline performance and ELT summary models. |
| Vector DB | `models/vector_db` | Job text and metadata prepared for Chroma embedding. |

The `vector_db` model produces `embedding_text` plus job metadata such as title, company, location, category, salary, source platform, and URL.

## Embedding Flow

```text
dbt vector_db model
    |
    v
tasks.process_tasks.getting_data_for_embedding_task
    |
    v
scripts.utils.embed_data_vector_db.embed_and_save_data
    |
    v
Chroma collection: CHROMA_COLLECTION_NAME
```

The Chroma embedding writer uses:

- `chromadb.HttpClient`
- `CHROMA_HOST`
- `CHROMA_PORT`
- `CHROMA_COLLECTION_NAME`
- `CHROMA_BATCH_SIZE`
- Chroma's `DefaultEmbeddingFunction`

The chatbot API uses the same collection and embedding function for query-time retrieval.

## Environment Variables

| Variable | Description |
| --- | --- |
| `AIRFLOW_WEBSERVER_PORT` | Host port for the Airflow web UI. |
| `AIRFLOW_WEBSERVER_SECRET_KEY` | Airflow webserver secret key. |
| `AIRFLOW_CONN_TRINO_DEFAULT` | Trino connection URI injected by Compose. |
| `TRINO_CONN_ID` | Connection id used by tasks that query Trino. |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection details. |
| `DB_AIRFLOW` | Airflow metadata database. |
| `DB_JOB` | Job data database. |
| `DB_TRINO` | Iceberg catalog metadata database. |
| `MINIO_USER`, `MINIO_PASSWORD` | MinIO credentials. |
| `MINIO_WAREHOUSE_BUCKET` | Warehouse bucket used by Trino/Iceberg. |
| `MINIO_CRAWLED_DATA_BUCKET` | Bucket for crawled data/object assets. |
| `CHROMA_HOST`, `CHROMA_PORT` | Chroma service connection details. |
| `CHROMA_COLLECTION_NAME`, `CHROMA_BATCH_SIZE` | Embedding target collection and insert batch size. |
| `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_DB` | MongoDB settings exposed for future/chatbot-related tasks. |
| `REDIS_HOST`, `REDIS_PORT` | Redis connection settings. |
| `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID` | Discord settings for job alert posting tasks. |
| `EMAIL`, `EMAIL_PASSWORD` | Placeholder email settings used by the current env template. |

## Running and Debugging

Start the full stack:

```bash
make run
```

Open Airflow:

```text
http://localhost:8080
```

Shell into the webserver container:

```bash
make docker-shell-airflow
```

Follow logs:

```bash
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
```

## Tests

Airflow helper tests live in `scripts/tests/` and are included by the root pytest config.

```bash
.venv/bin/python -m pytest infra/airflow/scripts/tests
```
