from typing import Any

DISCORD_LIMIT = 2000
SAFE_LIMIT = 1900


def split_discord_message(message: str, limit: int = SAFE_LIMIT) -> list[str]:
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
    title = job.get("title") or "Untitled job"
    company = job.get("company") or "Unknown company"
    locations = job.get("locations") or "Unknown location"
    salary = job.get("salary") or "Not specified"
    url = job.get("url") or ""
    return f"{index}. **{title}** - {company}\nLocation: {locations}\nSalary: {salary}\n{url}".strip()


def format_chat_response(payload: dict[str, Any]) -> str:
    answer = payload.get("answer") or "JobFlow chưa có câu trả lời."
    sources = payload.get("sources") or []
    source_lines = []
    for index, source in enumerate(sources[:5], start=1):
        title = source.get("title") or "Job"
        company = source.get("company") or "Company"
        url = source.get("url") or ""
        if url:
            source_lines.append(f"{index}. {title} - {company}: {url}")

    if not source_lines:
        return answer
    return f"{answer}\n\nSources:\n" + "\n".join(source_lines)


def format_jobs_response(payload: dict[str, Any]) -> str:
    jobs = payload.get("retrieved_jobs") or []
    if not jobs:
        return "JobFlow chưa tìm thấy job phù hợp trong Chroma."
    lines = [_job_line(job, index) for index, job in enumerate(jobs[:10], start=1)]
    return "Jobs found:\n\n" + "\n\n".join(lines)
