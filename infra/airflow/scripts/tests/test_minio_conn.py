import hashlib

import pytest

from scripts.utils.minio_conn import MinIOConnection


class FakeMinioClient:
    def __init__(self):
        self.uploads = []

    def bucket_exists(self, bucket_name):
        return True

    def put_object(self, bucket_name, object_name, data, length, content_type):
        self.uploads.append(
            {
                "bucket_name": bucket_name,
                "object_name": object_name,
                "data": data.read(),
                "length": length,
                "content_type": content_type,
            }
        )


def test_upload_file_uses_stable_hash_object_name_for_png():
    conn = object.__new__(MinIOConnection)
    conn.minio_client = FakeMinioClient()
    source_url = "https://example.com/logo.png"
    png_content = (
        b"\x89PNG\r\n\x1a\n" b"\x00\x00\x00\rIHDR" b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02" b"\x00\x00\x00\x90wS\xde"
    )

    object_name, mime = conn.upload_file("crawled-data", source_url, png_content)

    expected_hash = hashlib.md5(source_url.encode()).hexdigest()
    assert object_name == f"logos/{expected_hash}.png"
    assert mime == "png"
    assert conn.minio_client.uploads == [
        {
            "bucket_name": "crawled-data",
            "object_name": f"logos/{expected_hash}.png",
            "data": png_content,
            "length": len(png_content),
            "content_type": "image/png",
        }
    ]


def test_upload_file_rejects_unknown_image_type():
    conn = object.__new__(MinIOConnection)
    conn.minio_client = FakeMinioClient()

    with pytest.raises(ValueError, match="Unknown image type"):
        conn.upload_file("crawled-data", "https://example.com/logo", b"not an image")
