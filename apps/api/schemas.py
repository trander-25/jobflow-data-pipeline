from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for asking the chatbot a job-search question."""

    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class JobSearchRequest(BaseModel):
    """Request body for semantic job search without LLM generation."""

    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    user_id: str | None = Field(default=None, min_length=1)


class JobSource(BaseModel):
    """Job record returned from Chroma and exposed to API clients."""

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
    salary_min_million: str | int | float = ""
    salary_max_million: str | int | float = ""
    salary_avg_million: str | int | float = ""
    salary_band: str = ""
    posted_date: str = ""
    distance: float | None = None
    document: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceLink(BaseModel):
    """Compact source link included with chatbot and search responses."""

    job_id: str
    title: str = ""
    company: str = ""
    url: str = ""


class ChatResponse(BaseModel):
    """Response body for chatbot answers grounded in retrieved jobs."""

    answer: str
    sources: list[SourceLink]
    retrieved_jobs: list[JobSource]
    usage_context: dict[str, Any] = Field(default_factory=dict)


class JobSearchResponse(BaseModel):
    """Response body for job search results without an LLM answer."""

    answer: str = ""
    sources: list[SourceLink]
    retrieved_jobs: list[JobSource]
    usage_context: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Service health response for API dependency checks."""

    status: str
    chroma: str
    mongodb: str
    timestamp: datetime
