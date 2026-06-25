import os
import sys

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta

from airflow.decorators import dag
from tasks.tasks_group import topcv_pipeline

# Define DAG
default_args = {
    "owner": "trander",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


@dag(
    dag_id="topcv_pipeline",
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags=["topcv_pipeline"],
)
def _topcv_pipeline():
    """Build a standalone DAG for crawling and staging TopCV jobs."""
    topcv_pipeline()


dag = _topcv_pipeline()
