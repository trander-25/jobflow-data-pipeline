from minio import Minio
from minio.error import S3Error
from io import BytesIO
import os
import hashlib
import imghdr
import base64
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MinIOConnection:
    def __init__(self):
        self.minio_client = self._connect_minio()

    def _connect_minio(self):
        """Establishes a connection to the MinIO server using credentials from environment variables."""
        endpoint = "localhost:9000"
        # endpoint = "minio:9000"
        logger.info("Connecting to MinIO at %s", endpoint)
        return Minio(
            endpoint,
            access_key=os.getenv("MINIO_USER"),
            secret_key=os.getenv("MINIO_PASSWORD"),
            secure=False
        )
    
    def upload_data_object(self, bucket_name: str, data_object: list[dict], destination_file: str):
        """Uploads a data object to MinIO as a JSON file.
        Args:
            bucket_name (str): The name of the MinIO bucket to upload to.
            data_object (list[dict]): The data object to upload, which will be serialized to JSON.
            destination_file (str): The destination file name in the bucket (e.g., 'crawled-data/itviec_jobs.json').
        """
        import json
        import io
        # Ensure the bucket exists, create if it doesn't
        try:
            logger.info("Checking bucket: %s", bucket_name)
            if self.minio_client.bucket_exists(bucket_name):
                logger.info("Bucket exists: %s", bucket_name)
            else:
                logger.info("Bucket does not exist. Creating bucket: %s", bucket_name)
                self.minio_client.make_bucket(bucket_name)
                logger.info("Bucket created: %s", bucket_name)
        except S3Error as e:
            logger.error("Failed to check or create bucket '%s': %s", bucket_name, e, exc_info=True)
            return False

        # Convert the data_object to JSON bytes and upload to MinIO
        try:
            logger.info("Uploading object to %s/%s", bucket_name, destination_file)
            json_string = json.dumps(data_object, ensure_ascii=False)
            json_bytes_raw = json_string.encode("utf-8")
            json_bytes = io.BytesIO(json_bytes_raw)

            self.minio_client.put_object(
                bucket_name,
                destination_file,
                json_bytes,
                length=len(json_bytes_raw),
                content_type="application/json"
            )
            logger.info("Upload successful: %s/%s", bucket_name, destination_file)
            return True
        except S3Error as e:
            logger.error("Upload failed: %s/%s. Error: %s", bucket_name, destination_file, e, exc_info=True)
            return False
