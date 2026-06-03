from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request

from api.config import get_settings
from api.schemas import ChatRequest, ChatResponse, HealthResponse, JobSearchRequest, JobSearchResponse
from api.services.chroma_store import ChromaJobStore, source_links
from api.services.history_store import MongoChatHistoryStore
from api.services.llm import GenAIClient
from api.services.prompt import build_prompt
from api.services.rate_limiter import InMemoryRateLimiter

app = FastAPI(title="JobFlow Chatbot API", version="1.0.0")


def _settings():
    return app.state.settings


def _top_k(requested: int | None) -> int:
    settings = _settings()
    value = requested or settings.rag_default_top_k
    return min(value, settings.rag_max_top_k)


def _rate_limit(key: str) -> dict[str, int]:
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
    if request.client and request.client.host:
        return request.client.host
    return "unknown-client"


@app.on_event("startup")
def startup() -> None:
    settings = get_settings()
    app.state.settings = settings
    app.state.rate_limiter = InMemoryRateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)
    app.state.job_store = ChromaJobStore(settings)
    app.state.history_store = MongoChatHistoryStore(settings)
    app.state.llm = GenAIClient(settings)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
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
    rate_context = {}
    if _settings().rate_limit_search_enabled:
        rate_key = f"jobs:{payload.user_id or _client_key(request)}"
        rate_context = _rate_limit(rate_key)

    top_k = _top_k(payload.top_k)
    jobs = app.state.job_store.search(payload.query, top_k)
    return JobSearchResponse(
        sources=source_links(jobs),
        retrieved_jobs=jobs,
        usage_context={"top_k": top_k, "retrieved_count": len(jobs), "llm_used": False, **rate_context},
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    rate_context = _rate_limit(f"chat:{request.user_id}")
    top_k = _top_k(request.top_k)
    history = app.state.history_store.recent_messages(request.user_id, _settings().chat_history_limit)
    jobs = app.state.job_store.search(request.message, top_k)
    prompt = build_prompt(request.message, jobs, history)

    try:
        answer = app.state.llm.generate(prompt)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    app.state.history_store.add_message(request.user_id, "user", request.message)
    app.state.history_store.add_message(request.user_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        sources=source_links(jobs),
        retrieved_jobs=jobs,
        usage_context={
            "top_k": top_k,
            "retrieved_count": len(jobs),
            "history_messages_used": len(history),
            "llm_model": _settings().google_genai_model,
            "llm_used": True,
            **rate_context,
        },
    )


@app.delete("/chat/history/{user_id}")
def clear_history(user_id: str) -> dict[str, int | str]:
    deleted = app.state.history_store.clear_user(user_id)
    return {"user_id": user_id, "deleted_messages": deleted}
