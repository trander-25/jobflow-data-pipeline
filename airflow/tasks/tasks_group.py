from airflow.decorators import task, task_group
from tasks.process_tasks import load_crawl_sources_url, scrape_source_job, insert_jobs_to_staging_layer, post_job_to_discord, insert_company_logos_to_staging_layer, download_logos_and_upload_to_minio, update_company_logos_in_staging_layer
from tasks.audit_tasks import dbt_task_callback, discord_task_callback, task_failure_callback, task_success_callback
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

PROJECT_DIR = '/opt/airflow/dbt/job_warehouse'
PROFILE_DIR = '/opt/airflow/dbt/job_warehouse'

# task group for itviec pipeline
# @task_group
# def itviec_pipeline():
#     @task(
#         on_success_callback=task_success_callback,
#         on_failure_callback=task_failure_callback
#     )
#     def load_itviec_url():
#         return load_crawl_sources_url(source_crawl="itviec")

#     @task(
#         on_success_callback=task_success_callback,
#         on_failure_callback=task_failure_callback
#     )
#     def scrape_itviec_job(sources: dict):
#         return scrape_source_job(sources=sources, source_crawl="itviec")

#     @task(
#         on_success_callback=task_success_callback,
#         on_failure_callback=task_failure_callback
#     )
#     def insert_jobs_itviec(data):
#         return insert_jobs_to_staging_layer(data_file_path=data['uploaded_file_path'], source_crawl="itviec")

#     get_source_task = load_itviec_url()
#     scrape_task = scrape_itviec_job(get_source_task)
#     insert_staging_task = insert_jobs_itviec(scrape_task)
    
#     return insert_staging_task