import os
import sys

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta

from airflow.decorators import dag
from tasks.tasks_group import (
    dbt_wh_pipeline,
    embedding_data_vector_db_group,
    itviec_pipeline,
    post_job_group,
    process_company_logos_group,
    topcv_pipeline,
)

default_args = {
    "owner": "trander",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


@dag(
    default_args=default_args,
    dag_id="master_job_elt",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    schedule=None,
    tags=[
        "master_dag",
        "itviec_pipeline",
        "topcv_pipeline",
        "upload_discord",
        "dbt_pipeline",
    ],
)
def master_elt():
    """Build the end-to-end job ELT DAG from crawling through audit reporting."""
    itviec_insert = itviec_pipeline()
    topcv_insert = topcv_pipeline()

    post_tasks = post_job_group()
    process_image_task = process_company_logos_group()
    dbt_tasks = dbt_wh_pipeline(run_audit_after_reports=False)
    embedding_tasks = embedding_data_vector_db_group()

    itviec_insert >> post_tasks["itviec"]
    topcv_insert >> post_tasks["topcv"]
    itviec_insert >> process_image_task["insert_logos"]
    topcv_insert >> process_image_task["insert_logos"]
    [itviec_insert, topcv_insert] >> dbt_tasks["start"]
    dbt_tasks["reports_end"] >> embedding_tasks["start"]
    embedding_tasks["end"] >> dbt_tasks["audit"]


dag = master_elt()
