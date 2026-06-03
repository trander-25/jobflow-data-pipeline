<div align="center">

# 🚀 JobFlow Data Pipeline

**A local lakehouse data pipeline for crawling, validating, transforming, and analyzing job market data.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache_Airflow-2.9.1-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![Trino](https://img.shields.io/badge/Trino-Query_Engine-DD00A1?style=for-the-badge&logo=trino&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.4-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Object_Storage-C72E49?style=for-the-badge&logo=minio&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Transformations-FF694B?style=for-the-badge&logo=dbt&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 📌 Overview

JobFlow Data Pipeline is an end-to-end local data platform that collects job postings from job platforms, stores raw and processed data, validates data quality, and builds analytics-ready models for job market reporting.

The project follows a lakehouse-style workflow:

1. Crawl job data from sources such as **TopCV** and **ITViec**.
2. Store operational data in **PostgreSQL** and object data in **MinIO**.
3. Query warehouse tables through **Trino** with an **Iceberg** catalog.
4. Transform data with **dbt** across bronze, silver, gold, reports, and audit layers.
5. Orchestrate everything with **Apache Airflow**.
6. Keep optional chatbot/RAG infrastructure available through **MongoDB**, **Redis**, and **Chroma**.

---

## ✨ Features

- 🕷️ Job crawlers built with Python, Selenium, and BeautifulSoup.
- 🌬️ Airflow DAGs for ingestion, processing, image handling, and dbt workflows.
- 🧪 Data validation support with Great Expectations.
- 🪣 MinIO buckets for warehouse and crawled data storage.
- 🧊 Trino + Iceberg warehouse schemas for analytical querying.
- 🧱 dbt models organized by bronze, silver, gold, reports, and audit layers.
- 🐘 PostgreSQL bootstrap scripts for Airflow metadata, job data, and catalog metadata.
- 🧠 Chroma vector database for local vector search and default embedding workflows.
- 🍃 MongoDB for chatbot conversation storage.
- ⚡ Redis for cache or queue-oriented extensions.
- 🔔 Discord integration for notification and posting workflows.
- 🐳 Docker Compose setup for local development.

---

## 🏗️ Architecture

```text
Job Sources
    |
    v
Python Crawlers
    |
    v
Airflow Orchestration
    |
    +--> PostgreSQL        Operational data, metadata, Airflow database
    |
    +--> MinIO             Object storage and warehouse files
    |
    +--> Chroma/MongoDB/Redis
    |                       Optional chatbot and RAG infrastructure
    |
    v
Trino + Iceberg           Lakehouse query layer
    |
    v
dbt Models                Bronze -> Silver -> Gold -> Reports -> Audit
```

| Layer | Technology | Purpose |
| --- | --- | --- |
| 🕷️ Ingestion | Python, Selenium, BeautifulSoup | Crawl job postings and company information. |
| 🌬️ Orchestration | Apache Airflow | Schedule, run, retry, and monitor pipelines. |
| 🧪 Validation | Great Expectations | Validate crawled data before downstream usage. |
| 🪣 Storage | MinIO | Store warehouse files and crawled objects. |
| 🧊 Query Engine | Trino, Iceberg | Query lakehouse tables with SQL. |
| 🐘 Metadata | PostgreSQL | Store Airflow, application, and catalog metadata. |
| 🧠 Vector Store | Chroma | Store embeddings for chatbot/RAG retrieval. |
| 🍃 Chat Storage | MongoDB | Store chatbot conversation messages. |
| ⚡ Cache | Redis | Cache or queue support for future services. |
| 🧱 Transformation | dbt | Build curated analytical models. |
| 🔔 Notification | Discord | Send or publish pipeline outputs. |

---

## 🧰 Tech Stack

| Category | Tools |
| --- | --- |
| Language | Python 3.12 |
| Workflow Orchestration | Apache Airflow 2.9.1 |
| Data Crawling | Selenium, BeautifulSoup, Requests |
| Data Quality | Great Expectations |
| Transformation | dbt Core, dbt-trino |
| Query Engine | Trino |
| Table Format / Catalog | Iceberg, JDBC catalog |
| Databases | PostgreSQL 16.4, MongoDB 8.0, Chroma 1.5.2, Redis 7.4 |
| Object Storage | MinIO |
| DevOps | Docker, Docker Compose, Makefile |
| Code Quality | Ruff, pytest, pre-commit |

---

## 📂 Project Structure

```text
.
├── infra/
│   ├── airflow/
│   │   ├── dags/              # Airflow DAG definitions
│   │   ├── dbt_jobflow/       # dbt project and analytics models
│   │   ├── scripts/           # Crawlers, validation, utilities, source configs
│   │   ├── tasks/             # Reusable Airflow task groups and task helpers
│   │   ├── config/            # Airflow configuration
│   │   ├── Dockerfile         # Airflow runtime image
│   │   └── requirements.txt   # Airflow image dependencies
│   ├── chroma/                # Chroma vector database compose config
│   ├── minio/                 # MinIO object storage compose config
│   ├── mongodb/               # MongoDB compose config and chat collection bootstrap
│   ├── postgresql/
│   │   ├── init_db/           # Database creation scripts
│   │   ├── init_schema_table/ # Job database schema/table scripts
│   │   └── init_wh_catalog/   # Iceberg JDBC catalog tables
│   ├── redis/                 # Redis compose config
│   └── trino/
│       ├── etc/               # Trino runtime and catalog configuration
│       └── init_schema/       # Warehouse schema initialization SQL
├── docker-compose.yml         # Local platform entrypoint with included service compose files
├── Makefile                   # Common development commands
├── requirements.txt           # Local Python dependencies
└── .env.example               # Environment variable template
```

---

## 🧱 dbt Data Layers

| Layer | Path | Description |
| --- | --- | --- |
| Bronze | `infra/airflow/dbt_jobflow/models/bronze` | Source-aligned staging tables. |
| Silver | `infra/airflow/dbt_jobflow/models/silver` | Cleaned and unified intermediate models. |
| Gold | `infra/airflow/dbt_jobflow/models/gold` | Facts and dimensions for analytics. |
| Reports | `infra/airflow/dbt_jobflow/models/reports` | Business-ready report tables. |
| Audit | `infra/airflow/dbt_jobflow/models/audit` | Pipeline performance and ELT summary models. |

---

## 🌐 Services

| Service | URL / Port | Description |
| --- | --- | --- |
| Airflow Webserver | http://localhost:8080 | Manage DAGs and monitor pipeline runs. |
| Trino | http://localhost:8081 | SQL query endpoint mapped to container port `8080`. |
| MinIO API | http://localhost:9000 | S3-compatible object storage API. |
| MinIO Console | http://localhost:9001 | Object storage web console. |
| Chroma | http://localhost:8000 | Vector database HTTP endpoint. |
| PostgreSQL | `localhost:5432` | Metadata, job data, and catalog database. |
| MongoDB | `localhost:27017` | Chatbot message database. |
| Redis | `localhost:6379` | Cache/queue service. |

Default local credentials are created from `.env.example` when `make run` creates `.env`.

---

## ⚙️ Prerequisites

Make sure these tools are installed:

- Docker
- Docker Compose
- Make
- Python 3.12, only needed for local linting and tests outside Docker

---

## 🚀 Quick Start

Clone the repository and start the full local platform:

```bash
git clone <repository-url>
cd jobflow-data-pipeline
make run
```

`make run` will:

- Create `.env` from `.env.example` when `.env` does not exist.
- Create required persistent Docker volumes when they do not exist.
- Build the Airflow image.
- Start PostgreSQL, Airflow, MinIO, Trino, and initialization containers.
- Start Chroma, MongoDB, and Redis.
- Print the local service URLs.

After the containers are healthy, open:

- Airflow: http://localhost:8080
- Trino: http://localhost:8081
- MinIO Console: http://localhost:9001
- Chroma: http://localhost:8000

---

## 🔐 Environment Variables

Create your local environment file:

```bash
cp .env.example .env
```

Important variables:

| Variable | Description |
| --- | --- |
| `DB_USER` / `DB_PASSWORD` | PostgreSQL and Airflow admin credentials. |
| `DB_HOST` / `DB_PORT` | PostgreSQL service host and port. |
| `DB_JOB` | Application job database name. |
| `DB_AIRFLOW` | Airflow metadata database name. |
| `DB_TRINO` | Trino/Iceberg catalog metadata database name. |
| `POSTGRES_HOST_PORT` | PostgreSQL host port exposed on your machine. |
| `MINIO_USER` / `MINIO_PASSWORD` | MinIO root credentials. |
| `MINIO_API_PORT` / `MINIO_CONSOLE_PORT` | MinIO host ports. |
| `TRINO_VERSION` / `TRINO_HOST_PORT` | Trino image version and host port. |
| `TRINO_CONN_ID` | Airflow connection id used by embedding tasks to query Trino. |
| `CHROMA_VERSION` / `CHROMA_HOST_PORT` | Chroma image version and host port. |
| `CHROMA_COLLECTION_NAME` / `CHROMA_BATCH_SIZE` | Chroma collection and batch size used by embedding tasks. |
| `MONGODB_VERSION` / `MONGODB_HOST_PORT` | MongoDB image version and host port. |
| `REDIS_VERSION` / `REDIS_HOST_PORT` | Redis image version and host port. |
| `AIRFLOW_WEBSERVER_SECRET_KEY` | Airflow webserver secret key. |
| `DISCORD_TOKEN` / `DISCORD_CHANNEL_ID` | Discord integration settings. |
| `*_VOLUME_NAME` | Stable Docker volume names for persistent services. |

For local Docker usage, the default values in `.env.example` are enough to start the stack.

PostgreSQL SQL init files read `DB_JOB` and `DB_TRINO` from the container environment, so changing those database names in a fresh environment will create matching databases and schemas. If volumes already exist, changing database names requires resetting the Postgres volume first.

---

## 🕹️ Common Commands

| Command | Description |
| --- | --- |
| `make help` | Show available commands. |
| `make run` | Set up `.env`, build images, and start all services. |
| `make docker-up` | Start services without rebuilding. |
| `make docker-up-build` | Build images and start services. |
| `make docker-ps` | Show running service status. |
| `make docker-logs` | Follow logs from all services. |
| `make docker-restart` | Restart all services. |
| `make docker-down` | Stop all services. |
| `make docker-volume-init` | Create the persistent Docker volumes used by Compose. |
| `make docker-shell-airflow` | Open a shell inside the Airflow webserver container. |
| `make install` | Install local Python dependencies into `.venv`. |
| `make format` | Format Python code with Ruff. |
| `make format-check` | Check Python formatting without changing files. |
| `make lint` | Run Ruff linting with auto-fix. |
| `make lint-check` | Check Python lint issues without changing files. |
| `make test` | Run pytest. |
| `make pre-commit-install` | Install local pre-commit hooks. |
| `make pre-commit-run` | Run pre-commit hooks against all files. |
| `make check` | Run formatting check, Ruff lint/fix, and pytest. |

---

## ▶️ Running Pipelines

1. Start the platform:

   ```bash
   make run
   ```

2. Open Airflow at http://localhost:8080.

3. Log in with the credentials from `.env`:

   - Username: value of `DB_USER`
   - Password: value of `DB_PASSWORD`

4. Enable and trigger the main DAG:

   ```text
   master_job_elt
   ```

The main DAG coordinates ITViec and TopCV crawlers, post-processing tasks, company logo processing, and dbt warehouse transformations.

---

## 🔎 Querying Data

You can query the warehouse through Trino after the stack is running and initialization has completed.

Example from inside the Trino container:

```bash
docker compose exec trino trino --server http://localhost:8080
```

Example SQL:

```sql
SHOW CATALOGS;
SHOW SCHEMAS FROM iceberg;
SHOW TABLES FROM iceberg.gold;
```

---

## 🧪 Local Development

Install dependencies into the local virtual environment:

```bash
python -m venv .venv
make install
```

Run quality checks:

```bash
make format
make lint
make test
```

Run all checks:

```bash
make check
```

---

## 🧹 Resetting Local Services

Stop containers:

```bash
make docker-down
```

If you need a completely fresh database and object storage state, remove Docker volumes manually after stopping the stack:

```bash
docker volume rm jobflow_postgres_data
docker volume rm jobflow_minio_data
docker volume rm jobflow_chroma_data
docker volume rm jobflow_mongodb_data
```

Then start again:

```bash
make run
```

---

## 🗺️ Roadmap

- Add more documented example Trino queries.
- Expand crawler source documentation.
- Add dbt lineage screenshots or generated docs.
- Improve pipeline observability and alerting.
- Add production deployment notes.

---

## 📄 License

This project is licensed under the terms in [LICENSE](LICENSE).
