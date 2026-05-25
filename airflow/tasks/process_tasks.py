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