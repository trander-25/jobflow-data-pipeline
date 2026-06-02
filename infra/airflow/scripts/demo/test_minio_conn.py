import logging

from scripts.utils.minio_conn import MinIOConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    minio_conn = MinIOConnection()
    bucket_name = "crawled-data"
    # source_file = r'/home/thevinh/repos/jobflow-data-pipeline/infra/airflow/scripts/source_topcv.json'
    destination_file = "it_viec/it_viec_jobs.json"
    data_object = [{"title": "Sample Job", "url": "http://example.com/job1"}]
    minio_conn.upload_data_object(
        bucket_name,
        destination_file=destination_file,
        data_object=data_object,
    )


if __name__ == "__main__":
    main()
    # python3 -m scripts.demo.test_minio_conn
