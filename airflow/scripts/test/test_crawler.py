import json
import logging
from typing import Dict, List, Optional
from scripts.crawl_scripts.crawler import Crawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ITVIEC_URL = "https://itviec.com/it-jobs/ai-engineer"
TOPCV_URL = "https://www.topcv.vn/tim-viec-lam-ai-engineer"
MAX_JOBS = 2

def run_crawler(source: str, url: str) -> List[Dict[str, Optional[str]]]:
    logger.info("Testing %s crawler with max_jobs=%s", source, MAX_JOBS)
    jobs = Crawler(source).crawler(url, max_jobs=MAX_JOBS)
    logger.info("%s crawler returned %s jobs", source, len(jobs))
    return jobs

def main() -> None:
    results = {
        "itviec": run_crawler("itviec", ITVIEC_URL),
        "topcv": run_crawler("topcv", TOPCV_URL),
    }

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
