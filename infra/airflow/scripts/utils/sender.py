import asyncio
import logging
import os
from typing import Any, List

from sqlalchemy import text

from .db_conn import DBConnection
from .formatter import job_to_embed

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

ALLOWED_JOB_TABLES = {"topcv_data_job", "itviec_data_job"}


def _job_table_ref(table_name: str) -> str:
    """Return a fully qualified staging table reference for an allowed job table."""
    if table_name not in ALLOWED_JOB_TABLES:
        raise ValueError(f"Unsupported job table: {table_name}")

    db_name = os.getenv("DB_JOB", "job_db")
    return f"{db_name}.staging.{table_name}"


def query_unposted_jobs(table_name: str):
    """Fetch jobs that have not yet been sent to Discord.

    Args:
        table_name: Allowed staging job table name.

    Returns:
        A tuple containing Discord-ready job dictionaries and their source URLs.
    """
    engine = DBConnection().engine
    salary_col = "salary" if table_name == "topcv_data_job" else "'Sign-in ITViec for details.'"
    table_ref = _job_table_ref(table_name)
    query = text(f"""
        SELECT title, url, logo_url as logo, working_location as location, {salary_col} as salary
        FROM {table_ref}
        WHERE posted_to_discord = FALSE
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()

    jobs = [dict(row) for row in rows]
    urls = [row["url"] for row in rows]

    return jobs, urls


def mark_jobs_as_posted(table_name: str, job_urls: list):
    """Mark successfully sent job URLs as posted in the staging table."""
    if not job_urls:
        return

    engine = DBConnection().engine
    table_ref = _job_table_ref(table_name)
    query = text(f"""
        UPDATE {table_ref}
        SET posted_to_discord = TRUE
        WHERE url = ANY(:urls)
    """)

    with engine.begin() as conn:
        conn.execute(query, {"urls": job_urls})


async def send_jobs(jobs: List[dict], token: str, channel_id: int, throttle: float = 0.5) -> Any:
    """Send job embeds to Discord with optional throttling between messages.

    Args:
        jobs: Job records formatted for Discord embeds.
        token: Discord bot token.
        channel_id: Target Discord channel id.
        throttle: Delay in seconds between messages.

    Returns:
        A tuple containing success and failure counts, or None when Discord cannot be initialized.
    """
    try:
        import discord
    except ImportError:
        logger.exception(
            "discord package is not installed — cannot send messages. Install 'discord.py' in the worker environment."
        )
        return

    intents = discord.Intents.none()
    client = discord.Client(intents=intents)

    try:
        await client.login(token)
        channel = await client.fetch_channel(channel_id)
    except Exception as e:
        logger.exception("Failed to connect or fetch channel: %s", e)
        try:
            await client.close()
        except Exception:
            pass
        return

    success_job_send = 0
    fail_job_send = 0
    try:
        for job in jobs:
            try:
                embed = job_to_embed(job)
                await channel.send(embed=embed)
                logger.info(f"Succeeded to send job: {job}")
                success_job_send += 1
                if throttle and throttle > 0:
                    await asyncio.sleep(throttle)
            except Exception:
                logger.exception("Failed to send one job message")
                fail_job_send += 1
    finally:
        try:
            await client.close()
        except Exception:
            logger.exception("Error closing Discord client")

    return success_job_send, fail_job_send


def send_job_alerts(jobs, token: str, channel_id: int):
    """Synchronously send job alerts to Discord from an Airflow Python task."""
    if not jobs:
        logger.info("No jobs to send")
        return

    job_sent_status = asyncio.run(send_jobs(jobs, token, channel_id))

    total_job_success_sent = job_sent_status[0]
    total_job_fail_sent = job_sent_status[1]

    return total_job_success_sent, total_job_fail_sent
