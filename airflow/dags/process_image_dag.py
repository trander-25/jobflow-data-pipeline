import os
import sys
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from airflow.decorators import dag
from datetime import datetime, timedelta
from tasks.tasks_group import process_company_logos_group

#Define DAG
default_args = {
    'owner': 'trander',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(seconds=30)
}

@dag(
    dag_id='image_processing_pipeline',
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags=['image_pipeline']
)

def _image_processing_pipeline():
    process_company_logos_group()

dag = _image_processing_pipeline()