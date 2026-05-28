from airflow.decorators import dag, task
from datetime import datetime, timedelta


@dag(
    dag_id='test_dag',
    start_date=datetime(2025, 1, 1),
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['test']
)

def test_dag():
    @task
    def print_hello():
        print("Hello, TRANDER!")

    @task
    def print_wellcome():
        print("Welcome, TRANDER!")
        
    print_hello() >> print_wellcome()

dag = test_dag()