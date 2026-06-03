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
- 🤖 FastAPI RAG backend for job-search chatbot responses.
- 🍃 MongoDB for chatbot conversation storage.
- 💬 Discord slash-command bot for interactive job Q&A.
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
├── apps/
│   ├── api/                  # FastAPI RAG backend for chatbot/job search
│   └── bot/                  # Discord slash-command bot
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

Folder-level documentation:

| Path | Documentation | What to read it for |
| --- | --- | --- |
| `apps/` | [`apps/README.md`](apps/README.md) | Application services overview and app runtime flow. |
| `apps/api/` | [`apps/api/README.md`](apps/api/README.md) | FastAPI endpoints, RAG logic, Chroma/MongoDB/GenAI env vars. |
| `apps/bot/` | [`apps/bot/README.md`](apps/bot/README.md) | Discord slash commands, bot env vars, API integration. |
| `infra/` | [`infra/README.md`](infra/README.md) | Infrastructure services, Compose files, platform data flow. |
| `infra/airflow/` | [`infra/airflow/README.md`](infra/airflow/README.md) | DAGs, dbt layers, crawlers, embedding flow, Airflow env vars. |

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
| Chatbot API | http://localhost:8100 | FastAPI RAG backend for Chroma retrieval and Gemma responses. |
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
- Chatbot API: http://localhost:8100

### Chatbot API and Discord Bot

The chatbot runtime is split into two services:

- `apps/api/`: FastAPI backend with `/health`, `/chat`, `/jobs/search`, and `/chat/history/{user_id}`.
- `apps/bot/`: Discord slash-command bot with `/ask`, `/jobs`, and `/reset`.

Before using `/ask`, make sure the embedding DAG has populated Chroma and set these variables in `.env`:

```bash
GOOGLE_API_KEY="your_google_ai_api_key"
GOOGLE_GENAI_MODEL="gemma-3-27b-it"
DISCORD_TOKEN="your_discord_token"
DISCORD_GUILD_ID="optional_test_guild_id"
```

For local development outside Docker:

```bash
make api-dev
make bot-dev
```

### Chatbot API Endpoints

Base URL when running through Docker Compose: `http://localhost:8100`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check API dependency status for Chroma and MongoDB. |
| `POST` | `/chat` | Run full RAG chat: retrieve jobs, load history, call Google GenAI, save history. |
| `POST` | `/jobs/search` | Search Chroma and return matching jobs without calling the LLM. |
| `DELETE` | `/chat/history/{user_id}` | Delete stored MongoDB chat history for a user. |

Example `/chat` request:

```json
{
  "user_id": "discord-user-id",
  "message": "Có job Data Engineer ở TP.HCM không?",
  "top_k": 5
}
```

Example `/jobs/search` request:

```json
{
  "query": "backend Python remote",
  "top_k": 5
}
```

All chatbot responses include `sources`, `retrieved_jobs`, and `usage_context` so readers can see which job records were retrieved.

### Discord Bot Commands

| Command | Backend endpoint | Purpose |
| --- | --- | --- |
| `/ask question` | `POST /chat` | Ask a natural-language question and receive a grounded AI answer with job sources. |
| `/jobs query` | `POST /jobs/search` | Search matching jobs and show title, company, location, salary, and URL. |
| `/reset` | `DELETE /chat/history/{user_id}` | Clear the current Discord user's stored chat history. |

---

## 🔐 Environment Variables

Create your local environment file:

```bash
cp .env.example .env
```

Important variables by subsystem:

### Discord and Chatbot Apps

| Variable | Default | Used by | Description |
| --- | --- | --- | --- |
| `DISCORD_BOT_ENABLED` | `false` | `apps/bot` | Enables Discord login. Defaults to false so `docker compose up -d` is stable before a real token is configured. |
| `DISCORD_TOKEN` | `your_discord_token` | Airflow posting tasks, `apps/bot` | Discord bot token. Required for the bot and Discord post tasks. |
| `DISCORD_CHANNEL_ID` | `your_discord_channel_id` | Airflow posting tasks | Channel id used by job alert posting tasks. |
| `DISCORD_GUILD_ID` | empty | `apps/bot` | Optional guild id for faster slash-command sync during development. |
| `API_HOST_PORT` | `8100` | Docker Compose | Host port exposed for `apps/api`. |
| `API_BASE_URL` | `http://api:8100` | `apps/bot` | Base URL the bot uses to call the API inside Docker. For local bot dev, use `http://localhost:8100`. |
| `API_TIMEOUT_SECONDS` | `45` | `apps/bot` | HTTP timeout for bot-to-API calls. |
| `GOOGLE_API_KEY` | empty | `apps/api` | Google AI API key. Required by `POST /chat`. |
| `GOOGLE_GENAI_MODEL` | `gemma-3-27b-it` | `apps/api` | Model id used by `google-genai`. |
| `GOOGLE_GENAI_TEMPERATURE` | `0.2` | `apps/api` | LLM generation temperature. |
| `RAG_DEFAULT_TOP_K` | `5` | `apps/api` | Default Chroma result count when request `top_k` is omitted. |
| `RAG_MAX_TOP_K` | `10` | `apps/api` | Maximum retrieval count enforced by the API. |
| `CHAT_HISTORY_LIMIT` | `6` | `apps/api` | Number of recent MongoDB messages loaded for prompt context. |
| `JOBS_DEFAULT_TOP_K` | `5` | `apps/bot` | Number of jobs requested by the `/jobs` command. |
| `RATE_LIMIT_ENABLED` | `true` | `apps/api` | Enables in-memory anti-spam throttling. |
| `RATE_LIMIT_REQUESTS` | `10` | `apps/api` | Maximum requests per key inside the configured window. |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | `apps/api` | Rolling window size in seconds. |
| `RATE_LIMIT_SEARCH_ENABLED` | `true` | `apps/api` | Applies rate limiting to `/jobs/search` in addition to `/chat`. |

### PostgreSQL and Airflow

| Variable | Default | Used by | Description |
| --- | --- | --- | --- |
| `POSTGRES_HOST_PORT` | `5432` | PostgreSQL Compose service | Host port exposed for PostgreSQL. |
| `DB_USER` | `user` | PostgreSQL, Airflow, dbt | Local database username and Airflow admin username. |
| `DB_PASSWORD` | `password` | PostgreSQL, Airflow, dbt | Local database password and Airflow admin password. |
| `DB_HOST` | `postgresql_db` | Airflow, dbt, app services in Docker | PostgreSQL service hostname. |
| `DB_PORT` | `5432` | Airflow, dbt | PostgreSQL container port. |
| `DB_JOB` | `job_db` | Crawlers, PostgreSQL init, dbt | Job application database. |
| `DB_AIRFLOW` | `airflow_db` | Airflow | Airflow metadata database. |
| `DB_TRINO` | `catalog_wh` | Trino/Iceberg | Iceberg JDBC catalog metadata database. |
| `AIRFLOW_WEBSERVER_PORT` | `8080` | Airflow Compose service | Host port for Airflow UI. |
| `AIRFLOW_WEBSERVER_SECRET_KEY` | `random_secret_key` | Airflow | Webserver secret key. |
| `TRINO_CONN_ID` | `trino_default` | Airflow | Airflow connection id used by embedding tasks to query Trino. |
| `EMAIL`, `EMAIL_PASSWORD` | `no_need` | Airflow env template | Placeholder values for email-related extensions. |

### MinIO and Trino

| Variable | Default | Used by | Description |
| --- | --- | --- | --- |
| `MINIO_VERSION` | image tag | MinIO Compose service | MinIO server image version. |
| `MINIO_MC_VERSION` | image tag | MinIO init service | MinIO client image version. |
| `MINIO_USER` | `user` | MinIO, Airflow, Trino | MinIO root/access username. |
| `MINIO_PASSWORD` | `password` | MinIO, Airflow, Trino | MinIO root/access password. |
| `MINIO_API_PORT` | `9000` | MinIO Compose service | Host port for S3-compatible API. |
| `MINIO_CONSOLE_PORT` | `9001` | MinIO Compose service | Host port for MinIO console. |
| `MINIO_WAREHOUSE_BUCKET` | `warehouse` | MinIO, Trino/Iceberg | Bucket for warehouse data. |
| `MINIO_CRAWLED_DATA_BUCKET` | `crawled-data` | Crawlers, MinIO | Bucket for crawled raw/object data. |
| `TRINO_VERSION` | `481` | Trino Compose service | Trino image version. |
| `TRINO_HOST_PORT` | `8081` | Trino Compose service | Host port for Trino HTTP. |

### Chroma, MongoDB, Redis, and Volumes

| Variable | Default | Used by | Description |
| --- | --- | --- | --- |
| `CHROMA_VERSION` | `1.5.2` | Chroma Compose service | Chroma image version. |
| `CHROMA_HOST` | `chroma` | Airflow, `apps/api` | Chroma hostname inside Docker. |
| `CHROMA_HOST_PORT` | `8000` | Chroma Compose service | Host port exposed for Chroma. |
| `CHROMA_PORT` | `8000` | Chroma, Airflow, `apps/api` | Chroma container/API port. |
| `CHROMA_LISTEN_ADDRESS` | `0.0.0.0` | Chroma | Listen address inside the container. |
| `CHROMA_PERSIST_PATH` | `/data` | Chroma | Persisted data path in the container. |
| `CHROMA_ALLOW_RESET` | `false` | Chroma | Whether Chroma reset API is allowed. |
| `CHROMA_COLLECTION_NAME` | `job_embeddings` | Airflow, `apps/api` | Job embedding collection used for RAG. |
| `CHROMA_BATCH_SIZE` | `20` | Airflow embedding task | Batch size for adding documents to Chroma. |
| `MONGODB_VERSION` | `8.0` | MongoDB Compose service | MongoDB image version. |
| `MONGODB_USERNAME` | `user` | MongoDB, `apps/api` | MongoDB username. |
| `MONGODB_PASSWORD` | `password` | MongoDB, `apps/api` | MongoDB password. |
| `MONGODB_DB` | `jobflow` | MongoDB, `apps/api` | Database containing `chat_messages`. |
| `MONGODB_AUTH_SOURCE` | `admin` | `apps/api` | MongoDB authentication database. |
| `MONGODB_CHAT_COLLECTION` | `chat_messages` | `apps/api` | Collection used for per-user chat history. |
| `MONGODB_HOST` | `mongodb` | Airflow env, `apps/api` | MongoDB hostname inside Docker. |
| `MONGODB_PORT` | `27017` | MongoDB, `apps/api` | MongoDB container port. |
| `MONGODB_HOST_PORT` | `27017` | MongoDB Compose service | Host port exposed for MongoDB. |
| `REDIS_VERSION` | `7.4.9-alpine` | Redis Compose service | Redis image version. |
| `REDIS_HOST` | `redis` | Airflow env | Redis hostname inside Docker. |
| `REDIS_PORT` | `6379` | Redis | Redis container port. |
| `REDIS_HOST_PORT` | `6379` | Redis Compose service | Host port exposed for Redis. |
| `POSTGRES_VOLUME_NAME` | `jobflow_postgres_data` | Docker | Persistent PostgreSQL volume. |
| `MINIO_VOLUME_NAME` | `jobflow_minio_data` | Docker | Persistent MinIO volume. |
| `CHROMA_VOLUME_NAME` | `jobflow_chroma_data` | Docker | Persistent Chroma volume. |
| `MONGODB_VOLUME_NAME` | `jobflow_mongodb_data` | Docker | Persistent MongoDB volume. |

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
