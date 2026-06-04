import logging
import os
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "job_embeddings")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_BATCH_SIZE = int(os.getenv("CHROMA_BATCH_SIZE", "100"))
DEFAULT_EMBEDDING_FUNCTION = embedding_functions.DefaultEmbeddingFunction()


def _metadata_value(value: Any) -> str | int | float | bool:
    """Normalize a metadata value into a Chroma-supported scalar type."""
    if isinstance(value, (str, int, float, bool)):
        return value
    if value is None:
        return ""
    return str(value)


def _job_metadata(item: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Build the Chroma metadata payload for one job record."""
    metadata_fields = [
        "job_id",
        "source_platform",
        "url",
        "job_title",
        "company_name",
        "job_locations",
        "job_category",
        "work_model_normalized",
        "work_arrangement_normalized",
        "experiences_level",
        "year_of_experiences",
        "salary",
        "salary_min_million",
        "salary_max_million",
        "salary_avg_million",
        "salary_band",
        "job_posted_date",
        "job_posted_timestamp",
    ]
    return {field: _metadata_value(item.get(field)) for field in metadata_fields}


def _batched(items: list[Any], batch_size: int):
    """Yield consecutive fixed-size batches from a list."""
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def _existing_ids(collection, ids: list[str]) -> set[str]:
    """Return job ids that already exist in a Chroma collection."""
    existing: set[str] = set()
    for id_batch in _batched(ids, CHROMA_BATCH_SIZE):
        result = collection.get(ids=id_batch)
        existing.update(result.get("ids", []))
    return existing


def embed_and_save_data(data: list[dict[str, Any]]) -> dict[str, int]:
    """Embed valid job records and insert only new documents into Chroma.

    Args:
        data: Lakehouse vector_db rows containing job_id and embedding_text.

    Returns:
        Counts for received, embedded, already existing, and invalid rows.
    """
    if not data:
        logger.info("No data provided for Chroma embedding.")
        return {"received": 0, "embedded": 0, "skipped_existing": 0, "skipped_invalid": 0}

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DEFAULT_EMBEDDING_FUNCTION,
        metadata={"hnsw:space": "cosine"},
    )

    valid_rows = []
    skipped_invalid = 0
    seen_ids: set[str] = set()
    for item in data:
        job_id = str(item.get("job_id") or "").strip()
        embedding_text = str(item.get("embedding_text") or "").strip()
        if not job_id or not embedding_text:
            skipped_invalid += 1
            continue
        if job_id in seen_ids:
            skipped_invalid += 1
            continue

        seen_ids.add(job_id)
        valid_rows.append({**item, "job_id": job_id, "embedding_text": embedding_text})

    if not valid_rows:
        logger.info("No valid rows to embed after validation.")
        return {
            "received": len(data),
            "embedded": 0,
            "skipped_existing": 0,
            "skipped_invalid": skipped_invalid,
        }

    existing_ids = _existing_ids(collection, [row["job_id"] for row in valid_rows])
    rows_to_embed = [row for row in valid_rows if row["job_id"] not in existing_ids]

    if not rows_to_embed:
        logger.info("All %s valid jobs already exist in Chroma.", len(valid_rows))
        return {
            "received": len(data),
            "embedded": 0,
            "skipped_existing": len(existing_ids),
            "skipped_invalid": skipped_invalid,
        }

    embedded_count = 0
    for batch in _batched(rows_to_embed, CHROMA_BATCH_SIZE):
        collection.add(
            ids=[row["job_id"] for row in batch],
            documents=[row["embedding_text"] for row in batch],
            metadatas=[_job_metadata(row) for row in batch],
        )
        embedded_count += len(batch)

    logger.info(
        "Embedded %s new jobs into Chroma collection '%s'. Skipped %s existing and %s invalid rows.",
        embedded_count,
        COLLECTION_NAME,
        len(existing_ids),
        skipped_invalid,
    )
    return {
        "received": len(data),
        "embedded": embedded_count,
        "skipped_existing": len(existing_ids),
        "skipped_invalid": skipped_invalid,
    }
