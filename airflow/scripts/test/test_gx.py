import logging
import os
import sys
from typing import Callable

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.validation.ge_runner import run_ge_validation
from scripts.validation.itviec import expectations as itviec_expectations
from scripts.validation.topcv import expectations as topcv_expectations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def valid_itviec_records() -> list[dict]:
    return [
        {
            "url": "https://itviec.com/it-jobs/data-engineer-1",
            "descriptions": "Build and maintain data pipelines.",
            "requirements": "Python, SQL, Airflow.",
        },
        {
            "url": "https://itviec.com/it-jobs/data-engineer-2",
            "descriptions": "Develop analytics datasets.",
            "requirements": "Spark, dbt, PostgreSQL.",
        },
    ]


def invalid_itviec_records() -> list[dict]:
    records = valid_itviec_records()
    records[1]["url"] = records[0]["url"]
    records[1]["requirements"] = None
    return records


def valid_topcv_records() -> list[dict]:
    return [
        {
            "url": "https://www.topcv.vn/viec-lam/data-engineer-1",
            "descriptions": "Design data ingestion workflows.",
            "requirements": "Python, SQL, cloud storage.",
            "experience": "2 years",
        },
        {
            "url": "http://www.topcv.vn/viec-lam/data-engineer-2",
            "descriptions": "Operate batch jobs and monitor quality.",
            "requirements": "Airflow, pandas, PostgreSQL.",
            "experience": "1 year",
        },
    ]


def invalid_topcv_records() -> list[dict]:
    records = valid_topcv_records()
    records[0]["url"] = "ftp://www.topcv.vn/viec-lam/data-engineer-1"
    records[1]["experience"] = None
    return records


def run_case(
    name: str,
    records: list[dict],
    expectation_fn: Callable,
    should_pass: bool,
) -> None:
    logger.info("Running case: %s", name)
    try:
        run_ge_validation(
            records=records,
            expectation_fn=expectation_fn,
            source_name=name,
        )
    except Exception as exc:
        if should_pass:
            logger.exception("[FAIL] %s should pass but raised an error", name)
            raise

        logger.info("[PASS] %s failed as expected: %s", name, exc)
        return

    if not should_pass:
        raise AssertionError(f"{name} should fail but validation passed")

    logger.info("[PASS] %s passed as expected", name)


def main() -> None:
    cases = [
        ("itviec_valid", valid_itviec_records(), itviec_expectations, True),
        ("itviec_invalid", invalid_itviec_records(), itviec_expectations, False),
        ("topcv_valid", valid_topcv_records(), topcv_expectations, True),
        ("topcv_invalid", invalid_topcv_records(), topcv_expectations, False),
    ]

    for name, records, expectation_fn, should_pass in cases:
        run_case(name, records, expectation_fn, should_pass)

    logger.info("All GE runner test cases finished")


if __name__ == "__main__":
    main()
    # python3 -m scripts/validation/test_val.py