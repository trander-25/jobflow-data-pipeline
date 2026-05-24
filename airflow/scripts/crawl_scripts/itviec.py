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
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._driver_path = ChromeDriverManager().install()

    # ---------------- DRIVER SETUP ---------------- #
    def _get_chrome_options(self) -> Options:
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
        logger.info("Initializing ChromeDriver...")
        return webdriver.Chrome(
            service=Service(self._driver_path),
            options=self._get_chrome_options()
        )

    def _extract_text(self, section) -> Optional[str]:
        try:
            items = section.find_all(["p", "li"], recursive=True)
            texts = [i.get_text() for i in items if i.get_text(strip=True)]
            return " ".join(texts) if texts else None
        except Exception:
            return None

    def _is_challenge_page(self, soup: BeautifulSoup) -> bool:
        title_text = (soup.title.get_text(strip=True) if soup.title else "").lower()
        body_text = soup.get_text(" ", strip=True).lower()
        challenge_signals = [
            "just a moment",
            "attention required",
            "verify you are human",
            "cf-challenge",
            "cloudflare",
        ]
        return any(sig in title_text or sig in body_text for sig in challenge_signals)

    def _load_detail_soup(self, driver: webdriver.Chrome, url: str) -> BeautifulSoup:
        driver.get(url)
        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.body.innerText.length") > 250
            )
        except TimeoutException:
            logger.warning(f"Timeout waiting for job details to load for URL: {url}")
        return BeautifulSoup(driver.page_source, "html.parser")

    def _apply_detail_data(
        self, data: Dict[str, Optional[str]], detail_soup: BeautifulSoup
    ) -> None:
        job_cat_div = detail_soup.find("div", string="Job Expertise:")
        data["job_cat"] = ", ".join(
            [job_cat.text.strip() for job_cat in job_cat_div.find_next("div").find_all("a")]
        ) if job_cat_div else None

        sections = detail_soup.find_all(
            "div", class_="imy-5 paragraph"
        )

        if len(sections) > 0:
            data["descriptions"] = self._extract_text(sections[0])
        if len(sections) > 1:
            data["requirements"] = self._extract_text(sections[1])

    def _retry_detail_with_fresh_driver(self, data: Dict[str, Optional[str]]) -> None:
        if not data["url"]:
            return

        retry_driver = self._init_driver()
        try:
            time.sleep(0.5 + random.uniform(0.5, 1.5))
            retry_soup = self._load_detail_soup(retry_driver, data["url"])
            if not self._is_challenge_page(retry_soup):
                self._apply_detail_data(data, retry_soup)
        finally:
            retry_driver.quit()

    def scrape_jobs(self, url: str, max_jobs: Optional[int] = None) -> List[Dict[str, Optional[str]]]:
        driver = self._init_driver()
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        jobs = soup.find_all("div", class_="ipy-2")
        if max_jobs is not None:
            jobs = jobs[:max_jobs]
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
                        detail_soup = self._load_detail_soup(detail_driver, data["url"])
                        self._apply_detail_data(data, detail_soup)

                        if (
                            self._is_challenge_page(detail_soup)
                            or not data["descriptions"]
                            or not data["requirements"]
                        ):
                            logger.warning(
                                f"Retrying job detail with a fresh driver for URL: {data['url']}"
                            )
                            self._retry_detail_with_fresh_driver(data)

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
