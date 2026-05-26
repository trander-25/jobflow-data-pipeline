import os
import sys
import logging
import json
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def load_crawl_sources_url(source_crawl:str):
    """Load crawl sources from a JSON file based on the source_crawl parameter.
    Args:
        source_crawl (str): The source to crawl, either 'itviec' or 'topcv'.
    Returns:
        List[Dict]: A list of crawl sources loaded from the JSON file."""
    from scripts.utils.load_crawl_source import load_crawl_sources

    if source_crawl=='itviec':
        data = load_crawl_sources(file_name='source_itviec.json')
    elif source_crawl=='topcv':
        data = load_crawl_sources(file_name='source_topcv.json')
    else:
        raise ValueError(f"Unknown source_crawl: {source_crawl}. Must be 'itviec' or 'topcv'")
    
    if not data:
        raise ValueError(f"Failed to load crawl sources for {source_crawl}")
    return data

def upload_crawl_data_to_minio(data:List[Dict], source_crawl:str, bucket_name:str='crawled-data'):
    """Upload crawl data to MinIO.
    Args:
        data (List[Dict]): The crawl data to upload.
        source_crawl (str): The source of the crawl data, used for naming the destination file.
        bucket_name (str): The name of the MinIO bucket to upload to. Default is 'crawled-data'.
    Returns:
        str: The destination file path in MinIO where the data was uploaded."""
    import datetime
    if not data:
        logger.info(f"No {source_crawl} jobs to upload to MinIO")
        return {}

    from scripts.utils.minio_conn import MinIOConnection

    minio_conn = MinIOConnection()
    destination_file = f"{source_crawl}/{source_crawl}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_jobs.json"

    try:
        minio_conn.upload_data_object(bucket_name=bucket_name, destination_file=destination_file, data_object=data)
        logger.info(f"Uploaded {len(data)} {source_crawl} jobs to MinIO at {destination_file}")
        return destination_file
    except Exception as e:
        logger.error(f"Error uploading {source_crawl} jobs to MinIO: {e}")
        raise

def deduplicate_jobs(jobs: list[dict], key: str = "url") -> list[dict]:
    """Deduplicate a list of job dictionaries based on a specified key (default is 'url').
    Args:
        jobs (list[dict]): The list of job dictionaries to deduplicate.
        key (str): The key in the job dictionaries to use for deduplication. Default is 'url'.
    Returns:
        list[dict]: A deduplicated list of job dictionaries."""
    seen = set()
    deduped = []

    for job in jobs:
        if not isinstance(job, dict):
            continue

        value = job.get(key)
        if not value:
            continue

        if value not in seen:
            seen.add(value)
            deduped.append(job)

    return deduped

def scrape_source_job(sources: dict, source_crawl:str):
    """Scrape job data from specified sources, validate the data, and upload it to MinIO.
    Args:
        sources (dict): A dictionary of sources to scrape, where keys are source names and values are URLs.
        source_crawl (str): The source to crawl, either 'itviec' or 'topcv'.
    Returns:
        dict: A dictionary containing the results of the scraping process, including counts of rows processed,"""
    from scripts.crawl_scripts.crawler import Crawler
    from scripts.validation.ge_runner import run_ge_validation
    from scripts.validation.itviec import expectations as itviec_expectations
    from scripts.validation.topcv import expectations as topcv_expectations

    crawler = Crawler(source_crawl)
    total_data_job = []
    errors = []

    # Scrape jobs from each source and accumulate results
    for source, url in sources.items():
        logger.info(f"Processing source: {source} with URL: {url}")
        try:
            dict_jobs = crawler.crawler(url)
            if dict_jobs:
                logger.info(f"Successfully scraped {len(dict_jobs)} jobs from {source_crawl}")
                total_data_job += dict_jobs
        except Exception as e:
            logger.error(f"Error scraping {source_crawl} from {source}: {e}")
            errors.append(str(e))
    if errors and not total_data_job:
        raise RuntimeError(f"Failed to scrape any jobs from {source_crawl}. Errors: {errors}")
    
    deduped_jobs = deduplicate_jobs(total_data_job)
    
    source_expectations = itviec_expectations if source_crawl=='itviec' else topcv_expectations
    run_ge_validation(
        records=deduped_jobs,
        expectation_fn=source_expectations,
        source_name=source_crawl
    )
    
    upload_file_path = upload_crawl_data_to_minio(data=deduped_jobs, source_crawl=source_crawl)
    return_dict = {
            'rows_processed': 0,
            'rows_inserted': 0,
            'rows_scraped':len(deduped_jobs),
            'posts_sent': 0,
            'uploaded_file_path': upload_file_path
        }
    return return_dict