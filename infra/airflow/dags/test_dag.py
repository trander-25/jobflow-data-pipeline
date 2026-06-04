from datetime import datetime, timedelta

from airflow.decorators import dag, task


@dag(
    dag_id="test_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=["test"],
)
def test_dag():
    """Build a simple smoke-test DAG used to verify Airflow task execution."""

    @task
    def print_hello():
        """Print the first smoke-test message."""
        print("Hello, TRANDER!")

    @task
    def print_wellcome():
        """Print the second smoke-test message."""
        print("Welcome, TRANDER!")

    print_hello() >> print_wellcome()


dag = test_dag()
