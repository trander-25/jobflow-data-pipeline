from api.schemas import JobSource

SYSTEM_INSTRUCTIONS = """You are JobFlow Assistant, an AI chatbot for Vietnamese job search on Discord.
Answer in Vietnamese by default. If the user asks in English, answer in English.
Use only the retrieved job context and the conversation history.
If the context is empty or not enough, say that JobFlow has not found enough matching job data yet.
Do not invent company names, salaries, locations, URLs, or requirements.
When recommending jobs, include concise reasons and mention source URLs when available.
Do not add a separate "Sources" section.
For job recommendations, use this compact format:
1. **Job title** - Company
   Salary: salary if available
   Location: location if available
   Experience: experience if available
   Why: one short reason
   Link: source URL
If the user asks for a specific number of jobs, answer with exactly that many jobs when enough matching jobs exist.
"""


def build_context(jobs: list[JobSource]) -> str:
    """Format retrieved jobs into compact context text for the LLM prompt."""
    if not jobs:
        return "No retrieved jobs."

    lines: list[str] = []
    for index, job in enumerate(jobs, start=1):
        lines.append(
            "\n".join(
                [
                    f"[{index}] {job.title or 'Untitled job'}",
                    f"Company: {job.company}",
                    f"Source: {job.source_platform}",
                    f"Location: {job.locations}",
                    f"Category: {job.category}",
                    f"Experience: {job.experience_level} / {job.years_of_experience}",
                    f"Work: {job.work_arrangement} / {job.work_model}",
                    f"Salary: {job.salary} ({job.salary_band})",
                    f"Posted: {job.posted_date}",
                    f"URL: {job.url}",
                    f"Content: {job.document[:1200]}",
                ]
            )
        )
    return "\n\n".join(lines)


def build_prompt(message: str, jobs: list[JobSource], history: list[dict[str, str]]) -> str:
    """Build the full instruction, history, context, and question prompt."""
    history_text = "\n".join(f"{item['role']}: {item['message']}" for item in history) or "No prior messages."
    return f"""{SYSTEM_INSTRUCTIONS}

Conversation history:
{history_text}

Retrieved job context:
{build_context(jobs)}

User question:
{message}

Answer:"""
