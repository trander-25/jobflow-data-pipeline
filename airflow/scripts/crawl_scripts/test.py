import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from airflow.scripts.crawl_scripts.itviet import ITViecScraper


def main():
    url = "https://itviec.com/it-jobs/ai-engineer"
    scraper = ITViecScraper(headless=True)
    jobs = scraper.scrape_jobs(url)
    first_two_jobs = jobs[:2]

    print(f"Total jobs scraped (valid): {len(jobs)}")
    print("First 2 jobs:")
    print(json.dumps(first_two_jobs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
import time
import random
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from helpers.extracting_info import _safe_text, _safe_attr, _safe_find
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# ---------------- LOGGING ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ITViecScraper:
    """Scraper for ITviec.com job listings, specifically targeting data-related roles.
    This scraper uses Selenium to handle dynamic content and BeautifulSoup for parsing HTML.
    It extracts job details such as title, company, location, job category, tags, descriptions
    and requirements.

    Usage:
        scraper = ITViecScraper(headless=True)
        job_data = scraper.scrape_jobs("https://itviec.com/it-jobs/data-analyst")
    
    Note:
        - Ensure that the ChromeDriver is compatible with your installed version of Chrome.
        - The scraper includes error handling and logging for better traceability.
    """
    def __init__(self, headless: bool = True):
        """Initialize the scraper with optional headless mode for ChromeDriver."""
        self.headless = headless
        self._driver_path = ChromeDriverManager().install()

    # ---------------- DRIVER SETUP ---------------- #
    def _get_chrome_options(self) -> Options:
        """Configure Chrome options for Selenium WebDriver.
        Returns:
            Options: Configured Chrome options.
        """
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def _init_driver(self) -> webdriver.Chrome:
        """Initialize the Chrome WebDriver with the specified options.
        Returns:
            webdriver.Chrome: An instance of the Chrome WebDriver.
        """
        logger.info("Initializing ChromeDriver...")
        return webdriver.Chrome(
            service=Service(self._driver_path),
            options=self._get_chrome_options()
        )

    def _extract_text(self, section) -> Optional[str]:
        """Extract and concatenate text from a given BeautifulSoup section.
        Args:
            section: A BeautifulSoup element containing the job description or requirements.
        Returns:
            Optional[str]: A single string containing the concatenated text, or None if no text is found.
        """
        try:
            items = section.find_all(["p", "li"], recursive=True)
            texts = [i.get_text() for i in items if i.get_text(strip=True)]
            return " ".join(texts) if texts else None
        except Exception:
            return None

    def scrape_jobs(self, url: str) -> List[Dict[str, Optional[str]]]:
        driver = self._init_driver()
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        jobs = soup.find_all("div", class_="job-card")
        driver.quit()

        logger.info(f"Found {len(jobs)} jobs")
        job_data: List[Dict[str, Optional[str]]] = []

        detail_driver = self._init_driver()
        for idx, job in enumerate(jobs, 1):
            logger.info(f"Processing job {idx}/{len(jobs)}")

            data = {
                "title": None,
                "company": None,
                "logo": None,
                "url": None,
                "job_cat": None,
                "location": None,
                "mode": None,
                "tags": None,
                "descriptions": None,
                "requirements": None
            }

            try:
                url_el = _safe_find(job, "h3", class_="imt-3 text-break")
                raw_url = _safe_attr(url_el, "data-url")
                data["url"] = raw_url.split("?lab_feature=")[0] if raw_url else None

                if not data["url"]:
                    continue

                title_el = _safe_find(job, "h3")
                data["title"] = _safe_text(title_el)

                company_el = _safe_find(
                    job, "div", class_="imy-3 d-flex align-items-center"
                )
                data["company"] = _safe_text(
                    _safe_find(company_el, "span")
                )

                data["logo"] = _safe_attr(
                    _safe_find(company_el, "img"), "data-src"
                )

                data["mode"] = _safe_text(
                    _safe_find(job, "div", class_="text-rich-grey flex-shrink-0")
                )

                location_el = _safe_find(
                    job,
                    "div",
                    class_="text-rich-grey text-truncate text-nowrap stretched-link position-relative"
                )
                data["location"] = _safe_attr(location_el, "title")

                tag_container = _safe_find(
                    job, "div", class_="imt-4 imb-3 d-flex igap-1"
                )
                if tag_container:
                    tags = [
                        _safe_text(a)
                        for a in tag_container.find_all("a")
                        if _safe_text(a)
                    ]
                    data["tags"] = ", ".join(tags) if tags else None

                # -------- DETAIL PAGE (NEW DRIVER) -------- #
                if data["url"]:
                    try:
                        detail_driver.get(data["url"])
                        try:
                            WebDriverWait(detail_driver, 30).until(
                                lambda d: d.execute_script("return document.body.innerText.length") > 250
                            )
                        except TimeoutException:
                            logger.warning(f"Timeout waiting for job details to load for URL: {data['url']}")
                            #detail_driver.quit()
                            time.sleep(0.5 + random.uniform(0.5, 1.5))
                            continue

                        detail_soup = BeautifulSoup(
                            detail_driver.page_source, "html.parser"
                        )

                        job_cat_div = detail_soup.find("div", string="Job Expertise:")
                        
                        data["job_cat"] = ", ".join([job_cat.text.strip() for job_cat in job_cat_div.find_next("div").find_all("a")]) if job_cat_div else None

                        sections = detail_soup.find_all(
                            "div", class_="imy-5 paragraph"
                        )

                        if len(sections) > 0:
                            data["descriptions"] = self._extract_text(sections[0])
                        if len(sections) > 1:
                            data["requirements"] = self._extract_text(sections[1])

                    finally:
                        # detail_driver.quit()
                        detail_driver.delete_all_cookies()
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCache", {})
                        time.sleep(0.5 + random.uniform(0.5, 1.5))
            except Exception as e:
                logger.error(f"Job skipped due to unexpected error: {e}")
            
            if data['url'] and data['requirements'] and data['descriptions']:
                job_data.append(data)
        detail_driver.quit()
        
        logger.info(f"Scraping completed. Total jobs scraped: {len(job_data)}")
        return job_data