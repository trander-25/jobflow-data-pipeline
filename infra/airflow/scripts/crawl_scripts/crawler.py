from .itviec import ITViecScraper
from .topcv import TopCVScraper


class Crawler:
    """Dispatch job scraping to the implementation for a supported source.

    Args:
        source: Source platform name, for example "itviec" or "topcv".
    """

    def __init__(self, source):
        """Store the source platform used by the dispatcher."""
        self.source = source

    def crawler(self, url, max_jobs=None, max_jobs_page=None):
        """Run the scraper for the configured source.

        Args:
            url: Listing page URL to scrape.
            max_jobs: Optional maximum number of listing jobs to process.
            max_jobs_page: Optional maximum number of listing pages to scrape.

        Returns:
            Scraped job records from the selected source implementation.
        """
        if self.source == "itviec":
            return ITViecScraper().scrape_jobs(url, max_jobs=max_jobs, max_jobs_page=max_jobs_page)
        elif self.source == "topcv":
            return TopCVScraper().scrape_jobs(url, max_jobs=max_jobs, max_jobs_page=max_jobs_page)
        else:
            raise ValueError(f"Unsupported source: {self.source}")
