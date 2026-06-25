import re
import unicodedata
from dataclasses import dataclass

from api.schemas import JobSource

DEFAULT_RESPONSE_LIMIT = 5
MAX_RESPONSE_LIMIT = 10
SALARY_SCAN_LIMIT = 1000
SALARY_RETRIEVAL_LIMIT = 50

_VIETNAMESE_NUMBERS = {
    "mot": 1,
    "moot": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "tu": 4,
    "nam": 5,
    "sau": 6,
    "bay": 7,
    "tam": 8,
    "chin": 9,
    "muoi": 10,
}


@dataclass(frozen=True)
class QueryPlan:
    """Retrieval plan inferred from a user query and optional top_k override."""

    response_limit: int
    retrieval_limit: int
    salary_sort_desc: bool = False
    scan_salary_collection: bool = False


def normalize_text(value: str) -> str:
    """Lowercase and remove Vietnamese accents for lightweight query matching."""
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def requested_job_count(message: str) -> int | None:
    """Infer the number of requested jobs from Vietnamese or English text."""
    text = normalize_text(message)
    patterns = [
        r"\b(\d{1,2})\s*(?:job|jobs|viec|cong viec)\b",
        r"\b(?:top|lay|tim|cho toi|cho minh|goi y)\s*(\d{1,2})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    for word, value in _VIETNAMESE_NUMBERS.items():
        if re.search(rf"\b{word}\s+(?:job|jobs|viec|cong viec)\b", text):
            return value
    return None


def is_high_salary_query(message: str) -> bool:
    """Return True when a query asks for highest-paying jobs."""
    text = normalize_text(message)
    salary_terms = ("luong", "salary", "thu nhap", "income")
    high_terms = ("cao nhat", "highest", "top salary", "luong cao", "max salary")
    return any(term in text for term in salary_terms) and any(term in text for term in high_terms)


def plan_query(message: str, requested_top_k: int | None = None) -> QueryPlan:
    """Create a retrieval plan for semantic search or salary-oriented ranking."""
    requested_count = requested_top_k or requested_job_count(message)
    response_limit = min(requested_count or DEFAULT_RESPONSE_LIMIT, MAX_RESPONSE_LIMIT)
    salary_sort_desc = is_high_salary_query(message)

    if salary_sort_desc:
        return QueryPlan(
            response_limit=response_limit,
            retrieval_limit=max(SALARY_RETRIEVAL_LIMIT, response_limit),
            salary_sort_desc=True,
            scan_salary_collection=_is_broad_high_salary_query(message),
        )

    return QueryPlan(response_limit=response_limit, retrieval_limit=response_limit)


def salary_sort_value(job: JobSource) -> float:
    """Return the best available salary value for descending salary sorting."""
    values = [
        _number_value(job.salary_max_million),
        _number_value(job.salary_avg_million),
        _max_salary_from_text(job.salary),
    ]
    return max((value for value in values if value is not None), default=-1)


def sort_jobs_by_salary_desc(jobs: list[JobSource]) -> list[JobSource]:
    """Sort jobs with salary values first, ordered from highest to lowest."""
    salaried_jobs = [job for job in jobs if salary_sort_value(job) >= 0]
    unsalaried_jobs = [job for job in jobs if salary_sort_value(job) < 0]
    return sorted(salaried_jobs, key=salary_sort_value, reverse=True) + unsalaried_jobs


def _number_value(value: object) -> float | None:
    """Convert a numeric-like metadata value into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if value in (None, ""):
        return None
    normalized = str(value).strip().replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _max_salary_from_text(value: str) -> float | None:
    """Extract the maximum salary number from a free-form salary string."""
    text = normalize_text(value)
    if not text or any(term in text for term in ("thoa thuan", "canh tranh", "negotiable")):
        return None

    numbers = [float(item.replace(",", ".")) for item in re.findall(r"\d+(?:[,.]\d+)?", text)]
    if not numbers:
        return None

    max_value = max(numbers)
    if "usd" in text or "$" in text:
        return max_value * 25 / 1000
    return max_value


def _is_broad_high_salary_query(message: str) -> bool:
    """Detect broad highest-salary requests that should scan more of the collection."""
    text = normalize_text(message)
    text = re.sub(r"\b\d{1,2}\b", " ", text)
    filler_terms = [
        "job",
        "jobs",
        "viec",
        "cong viec",
        "cho toi",
        "cho minh",
        "tim",
        "kiem",
        "goi y",
        "top",
        "luong",
        "salary",
        "thu nhap",
        "income",
        "cao nhat",
        "highest",
        "cao",
        "max",
        "nhat",
        "co",
        "ra",
    ]
    for term in filler_terms:
        text = re.sub(rf"\b{re.escape(term)}\b", " ", text)
    return not text.strip()
