import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request

from api.config import get_settings
from api.schemas import ChatRequest, ChatResponse, HealthResponse, JobSearchRequest, JobSearchResponse, JobSource
from api.services.chroma_store import ChromaJobStore, source_links
from api.services.history_store import MongoChatHistoryStore
from api.services.llm import GenAIClient
from api.services.prompt import build_prompt
from api.services.query_planner import SALARY_SCAN_LIMIT, plan_query, sort_jobs_by_salary_desc
from api.services.rate_limiter import InMemoryRateLimiter, RedisRateLimiter

app = FastAPI(title="JobFlow Chatbot API", version="1.0.0")
logger = logging.getLogger(__name__)


def _settings():
    """Return the Settings object stored on FastAPI application state."""
    return app.state.settings


def _rate_limit(key: str) -> dict[str, int]:
    """Apply request throttling for a logical rate-limit key.

    Args:
        key: Endpoint-specific key such as "chat:<user_id>" or "jobs:<user_or_ip>".

    Returns:
        Remaining request count to include in response usage context.
    """
    settings = _settings()
    if not settings.rate_limit_enabled:
        return {"rate_limit_remaining": settings.rate_limit_requests}

    decision = app.state.rate_limiter.check(key)
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded. Please wait before sending another request.",
                "retry_after_seconds": decision.retry_after_seconds,
            },
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )
    return {"rate_limit_remaining": decision.remaining}


def _client_key(request: Request) -> str:
    """Return a stable fallback key for anonymous search requests."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown-client"


def _llm_fallback_answer() -> str:
    """Return a user-facing fallback answer when LLM generation is unavailable."""
    return (
        "JobFlow AI hiện chưa thể tạo câu trả lời vì dịch vụ GenAI đang không sẵn sàng. "
        "Mình vẫn gửi các job liên quan tìm được từ dữ liệu JobFlow bên dưới."
    )


def _retrieve_jobs(message: str, requested_top_k: int | None) -> tuple[list[JobSource], dict[str, int | bool | str]]:
    """Retrieve and optionally salary-sort jobs based on the query plan.

    Args:
        message: User query or chat message.
        requested_top_k: Optional explicit result count from the API request.

    Returns:
        Retrieved job records and retrieval metadata for response usage_context.
    """
    plan = plan_query(message, requested_top_k)
    if plan.scan_salary_collection and hasattr(app.state.job_store, "all_jobs"):
        candidates = app.state.job_store.all_jobs(limit=SALARY_SCAN_LIMIT)
        retrieval_mode = "salary_collection_scan"
    else:
        candidates = app.state.job_store.search(message, plan.retrieval_limit)
        retrieval_mode = "semantic_search"

    if plan.salary_sort_desc:
        candidates = sort_jobs_by_salary_desc(candidates)

    jobs = candidates[: plan.response_limit]
    return jobs, {
        "requested_count": plan.response_limit,
        "retrieval_limit": plan.retrieval_limit,
        "retrieval_mode": retrieval_mode,
        "salary_sort_desc": plan.salary_sort_desc,
    }


@app.on_event("startup")
def startup() -> None:
    """Initialize shared API services and dependency clients on application startup."""
    settings = get_settings()
    app.state.settings = settings
    try:
        app.state.rate_limiter = RedisRateLimiter(settings)
        app.state.rate_limiter.healthcheck()
    except Exception:
        logger.exception("Redis rate limiter unavailable; falling back to in-memory rate limiter")
        app.state.rate_limiter = InMemoryRateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)
    app.state.job_store = ChromaJobStore(settings)
    app.state.history_store = MongoChatHistoryStore(settings)
    app.state.llm = GenAIClient(settings)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return API dependency health for Chroma and MongoDB."""
    chroma_status = "ok"
    mongodb_status = "ok"

    try:
        app.state.job_store.healthcheck()
    except Exception:
        chroma_status = "unavailable"

    try:
        app.state.history_store.healthcheck()
    except Exception:
        mongodb_status = "unavailable"

    status = "ok" if chroma_status == "ok" and mongodb_status == "ok" else "degraded"
    return HealthResponse(
        status=status,
        chroma=chroma_status,
        mongodb=mongodb_status,
        timestamp=datetime.now(timezone.utc),
    )


@app.post("/jobs/search", response_model=JobSearchResponse)
def search_jobs(payload: JobSearchRequest, request: Request) -> JobSearchResponse:
    """Search jobs from Chroma without calling the LLM."""
    rate_context = {}
    if _settings().rate_limit_search_enabled:
        rate_key = f"jobs:{payload.user_id or _client_key(request)}"
        rate_context = _rate_limit(rate_key)

    jobs, retrieval_context = _retrieve_jobs(payload.query, payload.top_k)
    return JobSearchResponse(
        sources=source_links(jobs),
        retrieved_jobs=jobs,
        usage_context={"retrieved_count": len(jobs), "llm_used": False, **retrieval_context, **rate_context},
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Answer a user question with retrieved job context and persisted chat history."""
    rate_context = _rate_limit(f"chat:{request.user_id}")
    history = app.state.history_store.recent_messages(request.user_id, _settings().chat_history_limit)
    jobs, retrieval_context = _retrieve_jobs(request.message, request.top_k)
    prompt = build_prompt(request.message, jobs, history)

    llm_error = None
    try:
        answer = app.state.llm.generate(prompt)
        llm_used = True
    except ValueError as exc:
        logger.exception("LLM configuration failed")
        answer = _llm_fallback_answer()
        llm_used = False
        llm_error = str(exc)
    except Exception as exc:
        logger.exception("LLM generation failed")
        answer = _llm_fallback_answer()
        llm_used = False
        llm_error = f"Google GenAI request failed for model '{_settings().google_genai_model}': {exc}"

    app.state.history_store.add_message(request.user_id, "user", request.message)
    app.state.history_store.add_message(request.user_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        sources=source_links(jobs),
        retrieved_jobs=jobs,
        usage_context={
            "retrieved_count": len(jobs),
            "history_messages_used": len(history),
            "llm_model": _settings().google_genai_model,
            "llm_used": llm_used,
            "llm_error": llm_error,
            **retrieval_context,
            **rate_context,
        },
    )


@app.delete("/chat/history/{user_id}")
def clear_history(user_id: str) -> dict[str, int | str]:
    """Delete stored chat history for one user."""
    deleted = app.state.history_store.clear_user(user_id)
    return {"user_id": user_id, "deleted_messages": deleted}
