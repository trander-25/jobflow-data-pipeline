import logging

from airflow.decorators import task, task_group
from tasks.audit_tasks import (
    dbt_task_callback,
    discord_task_callback,
    task_failure_callback,
    task_success_callback,
)
from tasks.process_tasks import (
    download_logos_and_upload_to_minio,
    embed_and_save_data_task,
    getting_data_for_embedding_task,
    insert_company_logos_to_staging_layer,
    insert_jobs_to_staging_layer,
    load_crawl_sources_url,
    post_job_to_discord,
    scrape_source_job,
    update_company_logos_in_staging_layer,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

PROJECT_DIR = "/opt/airflow/dbt_jobflow"
PROFILE_DIR = "/opt/airflow/dbt_jobflow"
DBT_RUNTIME_ARGS = "--log-path /tmp/dbt_logs --target-path /tmp/dbt_target"


# task group for itviec pipeline
@task_group
def itviec_pipeline(max_jobs: int | None = 100, max_jobs_page: int | None = 9):
    """Build the ITViec crawl pipeline from source loading through staging insert."""

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def load_itviec_url():
        """Load ITViec listing URLs from the Airflow scripts configuration."""
        return load_crawl_sources_url(source_crawl="itviec")

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def scrape_itviec_job(sources: dict):
        """Scrape ITViec jobs and upload validated records to MinIO."""
        return scrape_source_job(
            sources=sources,
            source_crawl="itviec",
            max_jobs=max_jobs,
            max_jobs_page=max_jobs_page,
        )

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def insert_jobs_itviec(data):
        """Insert scraped ITViec jobs from MinIO into the staging table."""
        return insert_jobs_to_staging_layer(data_file_path=data["uploaded_file_path"], source_crawl="itviec")

    get_source_task = load_itviec_url()
    scrape_task = scrape_itviec_job(get_source_task)
    insert_staging_task = insert_jobs_itviec(scrape_task)

    return insert_staging_task


# task group for topcv pipeline
@task_group
def topcv_pipeline(max_jobs: int | None = 100, max_jobs_page: int | None = None):
    """Build the TopCV crawl pipeline from source loading through staging insert."""

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def load_topcv_url():
        """Load TopCV listing URLs from the Airflow scripts configuration."""
        return load_crawl_sources_url(source_crawl="topcv")

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def scrape_topcv_job(sources: dict):
        """Scrape TopCV jobs and upload validated records to MinIO."""
        return scrape_source_job(
            sources=sources,
            source_crawl="topcv",
            max_jobs=max_jobs,
            max_jobs_page=max_jobs_page,
        )

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def insert_jobs_topcv(data):
        """Insert scraped TopCV jobs from MinIO into the staging table."""
        return insert_jobs_to_staging_layer(data_file_path=data["uploaded_file_path"], source_crawl="topcv")

    get_source_task = load_topcv_url()
    scrape_task = scrape_topcv_job(get_source_task)
    insert_staging_task = insert_jobs_topcv(scrape_task)

    return insert_staging_task


# task group for processing logos
@task_group
def process_company_logos_group():
    """Build the company-logo processing pipeline for newly discovered logo URLs."""

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def insert_company_logos():
        """Insert unseen logo URLs into the staging logo table."""
        return insert_company_logos_to_staging_layer()

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def download_and_upload_logos(data: list[dict]):
        """Download logo URLs and upload optimized logo files to MinIO."""
        return download_logos_and_upload_to_minio(data)

    @task(on_success_callback=task_success_callback, on_failure_callback=task_failure_callback)
    def update_company_logos(results: list[dict]):
        """Update staging logo records with processed logo payloads."""
        return update_company_logos_in_staging_layer(results)

    insert_logos_task = insert_company_logos()
    download_upload_task = download_and_upload_logos(insert_logos_task)
    update_logos_task = update_company_logos(download_upload_task)

    return {
        "insert_logos": insert_logos_task,
        "download_upload": download_upload_task,
        "update_logos": update_logos_task,
    }


# task group for discord post
@task_group
def post_job_group():
    """Build Discord posting tasks for new jobs from each source staging table."""

    @task(on_success_callback=discord_task_callback, on_failure_callback=task_failure_callback)
    def post_job_to_discord_itviec():
        """Post unposted ITViec jobs to Discord."""
        return post_job_to_discord(crawl_source="itviec")

    @task(on_success_callback=discord_task_callback, on_failure_callback=task_failure_callback)
    def post_job_to_discord_topcv():
        """Post unposted TopCV jobs to Discord."""
        return post_job_to_discord(crawl_source="topcv")

    itviec_task = post_job_to_discord_itviec()
    topcv_task = post_job_to_discord_topcv()

    return {"itviec": itviec_task, "topcv": topcv_task}


# task group for dbt
@task_group
def dbt_wh_pipeline(run_audit_after_reports: bool = True):
    """Build the dbt warehouse pipeline from seeds through reports and audit.

    Args:
        run_audit_after_reports: When True, audit runs immediately after reports.
            Master DAG sets this to False so embedding can run before audit.
    """

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def seed_mapping_tables():
        """Return the dbt command that seeds mapping tables."""
        logger.info("Starting seed mapping tables!!!")
        return (
            "dbt seed --select job_category_mapping vn_city_mapping "
            f"--project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"
        )

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def process_bronze_wh_layer():
        """Return the dbt command that builds bronze models."""
        logger.info("Starting process data to bronze layer!!!")
        return f"dbt run --select bronze --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def bronze_wh_layer_test_models():
        """Return the dbt command that tests bronze models."""
        logger.info("Starting process data to bronze layer!!!")
        return f"dbt test --select bronze --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def process_silver_wh_layer():
        """Return the dbt command that builds silver models."""
        logger.info("Starting process data to silver layer!!!")
        return f"dbt run --select silver --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def silver_wh_layer_test_models():
        """Return the dbt command that tests silver models."""
        logger.info("Starting process data to silver layer!!!")
        return f"dbt test --select silver --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def process_gold_wh_layer():
        """Return the dbt command that builds gold models."""
        logger.info("Starting process data to gold layer!!!")
        return f"dbt run --select gold --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def gold_wh_layer_test_models():
        """Return the dbt command that tests gold models."""
        logger.info("Starting process data to gold layer!!!")
        return f"dbt test --select gold --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def process_reports_wh_layer():
        """Return the dbt command that builds report models."""
        logger.info("Starting process data to reports layer!!!")
        return f"dbt run --select reports --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def reports_wh_layer_test_models():
        """Return the dbt command that tests report models."""
        logger.info("Starting test reports layer models!!!")
        return f"dbt test --select reports --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task.bash
    def process_audit_wh_layer():
        """Return the dbt command that builds audit models."""
        logger.info("Starting process data to audit layer!!!")
        return f"dbt run --select audit --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    seeds = seed_mapping_tables()
    bronze = process_bronze_wh_layer()
    test_bronze = bronze_wh_layer_test_models()
    silver = process_silver_wh_layer()
    test_silver = silver_wh_layer_test_models()
    gold = process_gold_wh_layer()
    test_gold = gold_wh_layer_test_models()
    reports = process_reports_wh_layer()
    test_reports = reports_wh_layer_test_models()
    audit = process_audit_wh_layer()
    seeds >> bronze >> test_bronze >> silver >> test_silver >> gold >> test_gold >> reports >> test_reports
    if run_audit_after_reports:
        test_reports >> audit

    return {"start": seeds, "reports_end": test_reports, "audit": audit, "end": audit}


@task_group
def embedding_data_vector_db_group():
    """Build the vector_db model and write fresh embeddings to Chroma."""

    @task.bash(on_success_callback=dbt_task_callback, on_failure_callback=task_failure_callback)
    def process_vector_db_layer():
        """Return the dbt command that builds the vector_db model."""
        logger.info("Starting process data to vector_db layer!!!")
        return f"dbt run --select vector_db --project-dir {PROJECT_DIR} --profiles-dir {PROFILE_DIR} {DBT_RUNTIME_ARGS}"

    @task(
        on_success_callback=task_success_callback,
        on_failure_callback=task_failure_callback,
    )
    def retrieve_data_from_lakehouse() -> list[dict]:
        """Read fresh vector_db records from the lakehouse for embedding."""
        data_for_embedding = getting_data_for_embedding_task()
        return data_for_embedding if data_for_embedding else []

    @task(
        on_success_callback=task_success_callback,
        on_failure_callback=task_failure_callback,
    )
    def embedding_data_vector_db(data: list[dict]):
        """Embed fresh vector_db records and save them to Chroma."""
        return embed_and_save_data_task(data)

    vector_db = process_vector_db_layer()
    data = retrieve_data_from_lakehouse()
    embedded = embedding_data_vector_db(data)
    vector_db >> data >> embedded

    return {"start": vector_db, "end": embedded}
