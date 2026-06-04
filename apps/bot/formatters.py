from typing import Any

DISCORD_LIMIT = 2000
SAFE_LIMIT = 1900


def split_discord_message(message: str, limit: int = SAFE_LIMIT) -> list[str]:
    """Split a message into chunks that fit Discord's message length limit."""
    if len(message) <= limit:
        return [message]

    chunks: list[str] = []
    current = ""
    for line in message.splitlines():
        next_value = f"{current}\n{line}" if current else line
        if len(next_value) <= limit:
            current = next_value
            continue
        if current:
            chunks.append(current)
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current = line
    if current:
        chunks.append(current)
    return chunks


def _job_line(job: dict[str, Any], index: int) -> str:
    """Format one retrieved job as a compact Discord-friendly text block."""
    title = job.get("title") or "Untitled job"
    company = job.get("company") or "Unknown company"
    locations = job.get("locations") or "Unknown location"
    salary = job.get("salary") or "Not specified"
    experience = job.get("experience_level") or "Not specified"
    url = job.get("url") or ""
    return (
        f"{index}. **{title}** - {company}\n"
        f"Salary: {salary}\n"
        f"Location: {locations}\n"
        f"Experience: {experience}\n"
        f"Link: {url}"
    ).strip()


def format_chat_response(payload: dict[str, Any]) -> str:
    """Format the API chat response for a Discord follow-up message."""
    return payload.get("answer") or "JobFlow chưa có câu trả lời."


def format_jobs_response(payload: dict[str, Any]) -> str:
    """Format job search results for the Discord /jobs command."""
    jobs = payload.get("retrieved_jobs") or []
    if not jobs:
        return "JobFlow chưa tìm thấy job phù hợp trong Chroma."
    lines = [_job_line(job, index) for index, job in enumerate(jobs[:10], start=1)]
    return "Các job phù hợp:\n\n" + "\n\n".join(lines)
