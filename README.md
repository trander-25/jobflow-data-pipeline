# JobFlow Data Pipeline

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-Orchestration-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![Trino](https://img.shields.io/badge/Trino-Query_Engine-DD00A1?style=for-the-badge&logo=trino&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Metadata-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Object_Storage-C72E49?style=for-the-badge&logo=minio&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Transformations-FF694B?style=for-the-badge&logo=dbt&logoColor=white)

JobFlow Data Pipeline is a local data platform for crawling job postings, storing raw and curated data, and querying analytics-ready datasets through Trino.

The project is designed around a modern lakehouse-style workflow: Airflow orchestrates jobs, Selenium-based crawlers collect job data, MinIO stores warehouse files, PostgreSQL stores operational and catalog metadata, Trino provides SQL access, and dbt organizes transformation layers.

## Architecture

| Layer | Tooling | Purpose |
| --- | --- | --- |
| 🕷️ Ingestion | Python, Selenium, BeautifulSoup | Crawl job listings from sources such as TopCV and ITViec. |
| 🌬️ Orchestration | Apache Airflow | Schedule, run, and monitor pipeline tasks. |
| 🪣 Object Storage | MinIO | Store warehouse data for Iceberg tables. |
| 🧊 Lakehouse Query | Trino, Iceberg | Query bronze, silver, gold, and audit schemas. |
| 🐘 Metadata | PostgreSQL | Store Airflow metadata, application data, and Iceberg JDBC catalog metadata. |
| 🧱 Transformations | dbt | Model curated datasets by analytics layer. |

## Repository Layout

```text
.
├── airflow/
│   ├── dbt_jobflow/          # dbt project
│   ├── requirements.txt      # Airflow image Python dependencies
│   └── scripts/              # Crawlers and source configs
├── postgresql/
│   ├── init_db/              # Database bootstrap scripts
│   ├── init_schema_table/    # Application schema/table initialization
│   └── init_wh_catalog/      # Warehouse catalog initialization
├── trino/
│   ├── etc/                  # Trino runtime configuration and catalogs
│   └── init_schema/          # Iceberg schema bootstrap SQL
├── docker-compose.yml
└── Dockerfile
```

## Services

| Service | Port | Notes |
| --- | --- | --- |
| Airflow Webserver | `8080` | Pipeline UI |
| Trino | `8081` | SQL query endpoint, mapped to container port `8080` |
| MinIO API | `9000` | S3-compatible object storage |
| MinIO Console | `9001` | Object storage UI |
| PostgreSQL | `5432` | Metadata and application database |

## Configuration Notes

- Trino loads its configuration from `./trino/etc:/etc/trino`.
- Trino initializes Iceberg schemas from `./trino/init_schema:/init_schema`.
- PostgreSQL bootstrap SQL files are mounted from the `postgresql/` folder into `/docker-entrypoint-initdb.d/`.
- The dbt project is mounted into Airflow at `/opt/airflow/dbt_jobflow`.
- Runtime credentials and database names are expected in `.env`; use `.env.example` as the template.

## Quick Start

```bash
docker compose up --build
```

After the containers are ready, open:

- Airflow: http://localhost:8080
- Trino: http://localhost:8081
- MinIO Console: http://localhost:9001

## Roadmap

- Add production DAG documentation.
- Document crawler source configuration.
- Add dbt model lineage and testing notes.
- Add example Trino queries for bronze, silver, and gold layers.
