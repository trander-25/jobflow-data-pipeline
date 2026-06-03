from typing import Any

from api.config import Settings
from api.schemas import JobSource, SourceLink


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if value is None:
        return ""
    return str(value)


def _first_batch(result: dict[str, Any], key: str) -> list[Any]:
    value = result.get(key) or []
    if not value:
        return []
    first = value[0]
    return first if isinstance(first, list) else value


def map_chroma_results(result: dict[str, Any]) -> list[JobSource]:
    ids = _first_batch(result, "ids")
    documents = _first_batch(result, "documents")
    metadatas = _first_batch(result, "metadatas")
    distances = _first_batch(result, "distances")

    jobs: list[JobSource] = []
    for index, job_id in enumerate(ids):
        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        document = documents[index] if index < len(documents) and documents[index] else ""
        distance = distances[index] if index < len(distances) else None
        jobs.append(
            JobSource(
                job_id=str(job_id),
                title=_metadata_value(metadata, "job_title"),
                company=_metadata_value(metadata, "company_name"),
                source_platform=_metadata_value(metadata, "source_platform"),
                url=_metadata_value(metadata, "url"),
                locations=_metadata_value(metadata, "job_locations"),
                category=_metadata_value(metadata, "job_category"),
                work_model=_metadata_value(metadata, "work_model_normalized"),
                work_arrangement=_metadata_value(metadata, "work_arrangement_normalized"),
                experience_level=_metadata_value(metadata, "experiences_level"),
                years_of_experience=metadata.get("year_of_experiences", ""),
                salary=_metadata_value(metadata, "salary"),
                salary_band=_metadata_value(metadata, "salary_band"),
                posted_date=_metadata_value(metadata, "job_posted_date"),
                distance=distance,
                document=str(document),
                metadata=metadata,
            )
        )
    return jobs


def source_links(jobs: list[JobSource]) -> list[SourceLink]:
    return [SourceLink(job_id=job.job_id, title=job.title, company=job.company, url=job.url) for job in jobs if job.url]


class ChromaJobStore:
    def __init__(self, settings: Settings):
        import chromadb
        from chromadb.utils import embedding_functions

        self.settings = settings
        self.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )

    def healthcheck(self) -> None:
        self.client.heartbeat()

    def search(self, query: str, top_k: int) -> list[JobSource]:
        result = self.collection.query(query_texts=[query], n_results=top_k)
        return map_chroma_results(result)
