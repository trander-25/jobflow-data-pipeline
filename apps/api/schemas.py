from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class JobSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    user_id: str | None = Field(default=None, min_length=1)


class JobSource(BaseModel):
    job_id: str
    title: str = ""
    company: str = ""
    source_platform: str = ""
    url: str = ""
    locations: str = ""
    category: str = ""
    work_model: str = ""
    work_arrangement: str = ""
    experience_level: str = ""
    years_of_experience: str | int | float = ""
    salary: str = ""
    salary_band: str = ""
    posted_date: str = ""
    distance: float | None = None
    document: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceLink(BaseModel):
    job_id: str
    title: str = ""
    company: str = ""
    url: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceLink]
    retrieved_jobs: list[JobSource]
    usage_context: dict[str, Any] = Field(default_factory=dict)


class JobSearchResponse(BaseModel):
    answer: str = ""
    sources: list[SourceLink]
    retrieved_jobs: list[JobSource]
    usage_context: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    chroma: str
    mongodb: str
    timestamp: datetime
