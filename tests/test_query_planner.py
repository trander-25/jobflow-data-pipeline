from api.schemas import JobSource
from api.services.query_planner import plan_query, salary_sort_value, sort_jobs_by_salary_desc


def test_plan_query_uses_requested_job_count():
    plan = plan_query("cho tôi 2 job lương cao nhất")

    assert plan.response_limit == 2
    assert plan.salary_sort_desc is True
    assert plan.scan_salary_collection is True


def test_plan_query_defaults_to_five_for_general_search():
    plan = plan_query("kiếm job data analyst phù hợp")

    assert plan.response_limit == 5
    assert plan.retrieval_limit == 5
    assert plan.salary_sort_desc is False


def test_plan_query_keeps_salary_search_semantic_when_filters_exist():
    plan = plan_query("cho tôi 3 job Python remote lương cao nhất")

    assert plan.response_limit == 3
    assert plan.salary_sort_desc is True
    assert plan.scan_salary_collection is False


def test_sort_jobs_by_salary_desc_parses_salary_text():
    jobs = [
        JobSource(job_id="low", title="Low", salary="10 - 20 Triệu"),
        JobSource(job_id="high", title="High", salary="25 - 50 Triệu"),
        JobSource(job_id="unknown", title="Unknown", salary="Thoả Thuận"),
    ]

    sorted_jobs = sort_jobs_by_salary_desc(jobs)

    assert [job.job_id for job in sorted_jobs] == ["high", "low", "unknown"]
    assert salary_sort_value(sorted_jobs[0]) == 50
