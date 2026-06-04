import os
import sys
from datetime import datetime, timedelta

from airflow.decorators import dag

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tasks.tasks_group import itviec_pipeline

default_args = {
    "owner": "trander",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


@dag(
    dag_id="itviec_pipeline",
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags=["itviec_pipeline"],
)
def _itviec_pipeline():
    """Build a standalone DAG for crawling and staging ITViec jobs."""
    itviec_pipeline()


dag = _itviec_pipeline()
