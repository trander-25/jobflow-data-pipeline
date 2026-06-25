import hashlib
import imghdr
import logging
import os
from io import BytesIO

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

logger = logging.getLogger(__name__)


class MinIOConnection:
    """Wrap MinIO object storage operations used by Airflow tasks."""

    def __init__(self):
        """Create a MinIO client for the Docker Compose MinIO service."""
        self.minio_client = self._connect_minio()

    def _connect_minio(self):
        """Connect to MinIO using credentials from environment variables."""
        endpoint = "minio:9000"
        logger.info("Connecting to MinIO at %s", endpoint)
        return Minio(
            endpoint,
            access_key=os.getenv("MINIO_USER"),
            secret_key=os.getenv("MINIO_PASSWORD"),
            secure=False,
        )

    def upload_data_object(self, bucket_name: str, data_object: list[dict], destination_file: str):
        """Upload a list of dictionaries to MinIO as a JSON object.

        Args:
            bucket_name: MinIO bucket to write to.
            data_object: Data that will be serialized to JSON.
            destination_file: Object name in the bucket, for example "itviec/itviec_jobs.json".

        Returns:
            True when the upload succeeds, otherwise False.
        """
        import io
        import json

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
                content_type="application/json",
            )
            logger.info("Upload successful: %s/%s", bucket_name, destination_file)
            return True
        except S3Error as e:
            logger.error("Upload failed: %s/%s. Error: %s", bucket_name, destination_file, e, exc_info=True)
            return False

    def read_file(self, bucket_name: str, object_name: str):
        """Read and decode a UTF-8 text object from MinIO."""
        response = None
        try:
            response = self.minio_client.get_object(bucket_name, object_name)

            data = response.read().decode("utf-8")
            return data
        except S3Error as e:
            logger.error(f"Error reading file: {e}")
        finally:
            if response:
                response.close()
                response.release_conn()

    def upload_file(self, bucket_name: str, source_url: str, content: bytes):
        """Upload binary image content to MinIO using a stable URL-derived object name.

        Args:
            bucket_name: MinIO bucket to write to.
            source_url: Original image URL used to create the stable object name.
            content: Raw image bytes.

        Returns:
            The MinIO object name and normalized image MIME subtype.
        """

        def _detect_extension(content: bytes) -> str:
            """Detect the image file extension from raw bytes."""
            img_type = imghdr.what(None, content)
            if not img_type:
                raise ValueError("Unknown image type")
            return img_type

        def _object_name(url: str, ext: str) -> str:
            """Create a deterministic logo object path from the source URL."""
            h = hashlib.md5(url.encode()).hexdigest()
            return f"logos/{h}.{ext}"

        ext = _detect_extension(content)
        object_name = _object_name(source_url, ext)
        try:
            self.minio_client.bucket_exists(bucket_name)
        except S3Error as e:
            logger.error(f"Error checking bucket: {e}")
            logger.info(f"Creating bucket: {bucket_name}")
            self.minio_client.make_bucket(bucket_name)
        try:
            self.minio_client.put_object(
                bucket_name,
                object_name=object_name,
                data=BytesIO(content),
                length=len(content),
                content_type=f"image/{ext}",
            )
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
        mime = "png" if ext.lower() == "png" else "jpeg"
        return object_name, mime
