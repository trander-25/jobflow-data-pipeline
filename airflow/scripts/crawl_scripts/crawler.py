from .topcv import TopCVScraper
from .itviec import ITViecScraper

class Crawler:
    """Crawler class to scrape job listings from different sources.
    Args:
        source (str): The source to crawl from (e.g., "itviec", "topcv").
    """
    def __init__(self, source):
        self.source = source

    def crawler(self, url, max_jobs=None):
        if self.source == "itviec":
            return ITViecScraper().scrape_jobs(url, max_jobs=max_jobs)
        elif self.source == "topcv":
            return TopCVScraper().scrape_jobs(url, max_jobs=max_jobs)
        else:
            raise ValueError(f"Unsupported source: {self.source}")
