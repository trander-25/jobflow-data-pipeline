import os
import sys

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta

from airflow.decorators import dag
from tasks.tasks_group import post_job_group

default_args = {
    "owner": "trander",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


@dag(
    default_args=default_args,
    dag_id="post_job_elt",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    schedule=None,
    tags=["upload_discord"],
)
def post_job_pipeline():
    post_job_group()


dag = post_job_pipeline()
