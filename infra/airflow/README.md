# Airflow Runtime

`infra/airflow/` is the orchestration layer for JobFlow. It builds the Airflow image, defines DAGs, runs crawlers and validation, executes dbt, processes images, posts Discord job alerts, and writes job embeddings to Chroma.

## Folder Contents

| Path | Purpose |
| --- | --- |
| `dags/` | Airflow DAG definitions. |
| `tasks/` | Reusable Airflow task and task-group helpers. |
| `scripts/crawl_scripts/` | TopCV and ITViec crawler implementations. |
| `scripts/validation/` | Great Expectations validation entry points for crawled sources. |
| `scripts/utils/` | Database, MinIO, embedding, formatting, image, and Discord helpers. |
| `scripts/source_*.json` | Source configuration consumed by crawler tasks. |
| `dbt_jobflow/` | dbt project for warehouse, report, audit, and vector-search models. |
| `config/airflow.cfg` | Airflow config mounted into containers. |
| `Dockerfile` | Airflow runtime image with Python dependencies and browser tooling for crawlers. |
| `docker-compose.airflow.yml` | Airflow init, webserver, and scheduler services. |
| `requirements.txt` | Python dependencies installed into the Airflow image. |

## DAGs

| DAG file | Purpose |
| --- | --- |
| `master_dag.py` | End-to-end orchestration for crawl, processing, dbt, and embedding stages. |
| `topcv_jobs.py` | TopCV crawl pipeline. |
| `itviec_jobs.py` | ITViec crawl pipeline. |
| `dbt_pipeline.py` | dbt transformation pipeline. |
| `embed_vector_db.py` | Build the `vector_db` model and embed rows into Chroma. |
| `post_job_dag.py` | Post unposted job alerts to Discord. |
| `process_image_dag.py` | Process company logo/image assets. |
| `test_dag.py` | Lightweight DAG used for Airflow sanity checks. |

## dbt Models

The dbt project lives in `dbt_jobflow/`.

| Layer | Path | Purpose |
| --- | --- | --- |
| Bronze | `models/bronze` | Source-aligned staging models. |
| Silver | `models/silver` | Cleaned and unified intermediate job models. |
| Gold | `models/gold` | Fact and dimension models. |
| Reports | `models/reports` | Business-ready report tables for Superset. |
| Audit | `models/audit` | ELT and task-performance summary models. |
| Vector DB | `models/vector_db` | Job text and metadata prepared for Chroma embedding. |

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

The API queries the same Chroma collection for `/jobs/search` and `/chat`.

## Running

Start the full stack from the project root:

```bash
make run
```

Open Airflow at http://localhost:8080, then trigger `master_job_elt` for the main workflow.

Useful debugging commands:

```bash
make docker-shell-airflow
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
```

## Configuration

Use the root [`.env.example`](../../.env.example) as the source of truth. Airflow mainly depends on `AIRFLOW_*`, `DB_*`, `MINIO_*`, `TRINO_CONN_ID`, `CHROMA_*`, and optional Discord posting variables.

## Tests

Airflow-related tests are under [`tests/airflow`](../../tests/airflow/).

```bash
.venv/bin/python -m pytest tests/airflow
```
