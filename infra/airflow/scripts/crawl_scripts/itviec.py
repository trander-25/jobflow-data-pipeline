import logging
import random
import time
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .helpers.extracting_info import _safe_attr, _safe_find, _safe_text

# ---------------- LOGGING ---------------- #
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------- SCRAPER SETTINGS ---------------- #
ITVIEC_LISTING_PAGE_LOAD_SECONDS = 3
ITVIEC_DETAIL_WAIT_TIMEOUT_SECONDS = 30
ITVIEC_DETAIL_MIN_BODY_TEXT_LENGTH = 250
ITVIEC_DETAIL_DRIVER_JOB_BATCH_SIZE = 10
ITVIEC_DETAIL_DELAY_MIN_SECONDS = 0.5
ITVIEC_DETAIL_DELAY_MAX_SECONDS = 1.5
ITVIEC_RETRY_DELAY_MIN_SECONDS = 0.5
ITVIEC_RETRY_DELAY_MAX_SECONDS = 1.5


class ITViecScraper:
    """Scrape ITViec listing pages and enrich records from job detail pages."""

    def __init__(self, headless: bool = True):
        """Initialize scraper options and resolve the ChromeDriver path."""
        self.headless = headless
        self._driver_path = ChromeDriverManager().install()

    # ---------------- DRIVER SETUP ---------------- #
    def _get_chrome_options(self) -> Options:
        """Build Chrome options used by the ITViec Selenium driver."""
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
        """Create a Selenium Chrome driver for ITViec pages."""
        logger.info("Initializing ChromeDriver...") 
        return webdriver.Chrome(service=Service(self._driver_path), options=self._get_chrome_options())

    def _preview_html(self, element, max_length: int = 500) -> str:
        """Return a compact HTML preview for scraper debug logs."""
        if element is None:
            return "<None>"

        html = " ".join(str(element).split())
        return html[:max_length] + "..." if len(html) > max_length else html

    def _listing_page_url(self, url: str, page: int) -> str:
        """Return a listing URL with the requested ITViec page query parameter."""
        parsed_url = urlparse(url)
        query_params = [
            (key, value)
            for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if key != "page"
        ]
        query_params.append(("page", str(page)))
        return urlunparse(parsed_url._replace(query=urlencode(query_params)))

    def _extract_total_pages(self, soup: BeautifulSoup) -> int:
        """Extract the last available listing page number from ITViec pagination."""
        pagination = soup.select_one(".pagination-search-jobs nav.ipagination")
        if pagination is None:
            return 1

        page_numbers = []
        for page_el in pagination.select("div.page"):
            page_classes = page_el.get("class", [])
            if "gap" in page_classes or "prev" in page_classes or "next" in page_classes:
                continue

            page_text = page_el.get_text(" ", strip=True)
            if page_text.isdigit():
                page_numbers.append(int(page_text))

            link_el = page_el.find("a", href=True)
            if link_el and link_el.get_text(strip=True).isdigit():
                page_numbers.append(int(link_el.get_text(strip=True)))

        return max(page_numbers, default=1)

    def _load_listing_soup(self, driver: webdriver.Chrome, url: str) -> tuple[BeautifulSoup, str]:
        """Load one ITViec listing page and parse it into BeautifulSoup."""
        driver.get(url)
        time.sleep(ITVIEC_LISTING_PAGE_LOAD_SECONDS)
        page_source = driver.page_source
        return BeautifulSoup(page_source, "html.parser"), page_source

    def _select_listing_jobs(
        self,
        soup: BeautifulSoup,
        page_source: str,
        url: str,
        remaining_jobs: Optional[int],
    ) -> List:
        """Select valid ITViec listing job blocks from one page."""
        is_listing_challenge = self._is_challenge_page(soup)
        job_candidates = soup.find_all("div", class_="ipy-2")
        jobs = [job for job in job_candidates if job.find("h3", attrs={"data-url": True})]
        filtered_blocks = [job for job in job_candidates if not job.find("h3", attrs={"data-url": True})]
        original_job_count = len(jobs)
        if remaining_jobs is not None:
            jobs = jobs[:remaining_jobs]

        logger.info(
            "Loaded ITViec listing | url=%s title=%r body_text_len=%s html_len=%s challenge=%s "
            "candidate_blocks=%s valid_job_blocks=%s filtered_blocks=%s selected_jobs=%s",
            url,
            soup.title.get_text(strip=True) if soup.title else None,
            len(soup.get_text(" ", strip=True)),
            len(page_source),
            is_listing_challenge,
            len(job_candidates),
            original_job_count,
            len(filtered_blocks),
            len(jobs),
        )
        for filtered_idx, filtered_block in enumerate(filtered_blocks[:3], 1):
            logger.info(
                "Filtered non-job ITViec listing block %s/%s | html_preview=%s",
                filtered_idx,
                len(filtered_blocks),
                self._preview_html(filtered_block),
            )
        if jobs:
            logger.info("First listing job HTML preview: %s", self._preview_html(jobs[0]))
            logger.info("Last listing job HTML preview: %s", self._preview_html(jobs[-1]))

        return jobs

    def _log_job_state(self, level: int, message: str, idx: int, total: int, data: Dict[str, Optional[str]]) -> None:
        """Log the current extraction state for one job record."""
        logger.log(
            level,
            "%s | job=%s/%s title=%r company=%r url=%r desc=%s req=%s job_cat=%r",
            message,
            idx,
            total,
            data.get("title"),
            data.get("company"),
            data.get("url"),
            bool(data.get("descriptions")),
            bool(data.get("requirements")),
            data.get("job_cat"),
        )

    def _extract_text(self, section) -> Optional[str]:
        """Extract joined paragraph and list-item text from a detail section."""
        try:
            items = section.find_all(["p", "li"], recursive=True)
            texts = [i.get_text() for i in items if i.get_text(strip=True)]
            return " ".join(texts) if texts else None
        except Exception as e:
            logger.warning("Failed to extract text from detail section: %s", e, exc_info=True)
            return None

    def _is_challenge_page(self, soup: BeautifulSoup) -> bool:
        """Detect Cloudflare or bot-protection challenge pages."""
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
        """Load an ITViec detail page and parse it into BeautifulSoup."""
        logger.info("Loading ITViec detail page: %s", url)
        driver.get(url)
        try:
            WebDriverWait(driver, ITVIEC_DETAIL_WAIT_TIMEOUT_SECONDS).until(
                lambda d: d.execute_script("return document.body.innerText.length")
                > ITVIEC_DETAIL_MIN_BODY_TEXT_LENGTH
            )
        except TimeoutException:
            logger.warning("Timeout waiting for job details to load for URL: %s", url)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        logger.info(
            "Loaded ITViec detail page | url=%s title=%r body_text_len=%s html_len=%s challenge=%s",
            url,
            soup.title.get_text(strip=True) if soup.title else None,
            len(soup.get_text(" ", strip=True)),
            len(page_source),
            self._is_challenge_page(soup),
        )
        return soup

    def _apply_detail_data(self, data: Dict[str, Optional[str]], detail_soup: BeautifulSoup) -> None:
        """Populate job category, description, and requirement fields from a detail page."""
        job_cat_div = detail_soup.find("div", string="Job Expertise:")
        data["job_cat"] = (
            ", ".join([job_cat.text.strip() for job_cat in job_cat_div.find_next("div").find_all("a")])
            if job_cat_div
            else None
        )

        sections = detail_soup.find_all("div", class_="imy-5 paragraph")
        logger.info(
            "Detail extraction summary | url=%r title=%r job_cat_found=%s section_count=%s",
            data.get("url"),
            data.get("title"),
            job_cat_div is not None,
            len(sections),
        )

        if len(sections) > 0:
            data["descriptions"] = self._extract_text(sections[0])
        if len(sections) > 1:
            data["requirements"] = self._extract_text(sections[1])

        logger.info(
            "Detail fields after extraction | url=%r descriptions_len=%s requirements_len=%s",
            data.get("url"),
            len(data["descriptions"]) if data.get("descriptions") else 0,
            len(data["requirements"]) if data.get("requirements") else 0,
        )

    def _retry_detail_with_fresh_driver(self, data: Dict[str, Optional[str]]) -> None:
        """Retry detail extraction with a fresh driver when the existing session is blocked."""
        if not data["url"]:
            logger.warning(
                "Skip detail retry because job URL is missing | title=%r company=%r",
                data.get("title"),
                data.get("company"),
            )
            return

        retry_driver = self._init_driver()
        try:
            logger.info("Retrying detail with fresh driver | url=%s title=%r", data["url"], data.get("title"))
            time.sleep(random.uniform(ITVIEC_RETRY_DELAY_MIN_SECONDS, ITVIEC_RETRY_DELAY_MAX_SECONDS))
            retry_soup = self._load_detail_soup(retry_driver, data["url"])
            is_challenge = self._is_challenge_page(retry_soup)
            if not is_challenge:
                self._apply_detail_data(data, retry_soup)
            else:
                logger.warning("Retry detail page is still a challenge page | url=%s", data["url"])
        finally:
            retry_driver.quit()

    def _close_driver(self, driver: webdriver.Chrome, reason: str) -> None:
        """Close a Chrome driver after best-effort cookie/cache cleanup."""
        try:
            driver.delete_all_cookies()
            driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
            driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        except Exception:
            logger.debug("Skipping driver cleanup before close | reason=%s", reason, exc_info=True)
        finally:
            logger.info("Closing ChromeDriver | reason=%s", reason)
            driver.quit()

    def _scrape_listing_job(
        self,
        detail_driver: webdriver.Chrome,
        job,
        idx: int,
        total: int,
    ) -> tuple[Optional[Dict[str, Optional[str]]], bool]:
        """Extract one listing job and enrich it from its detail page."""
        logger.info(
            "Processing ITViec listing job %s/%s | html_preview=%s",
            idx,
            total,
            self._preview_html(job, 350),
        )

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
            "requirements": None,
        }
        should_rotate_driver = False

        try:
            url_el = job.find("h3", attrs={"data-url": True})
            title_el = url_el or _safe_find(job, "h3")
            data["title"] = _safe_text(title_el)
            company_el = _safe_find(job, "div", class_="imy-3 d-flex align-items-center")
            data["company"] = _safe_text(_safe_find(company_el, "span"))

            if url_el is None:
                logger.warning(
                    "Missing URL element for ITViec job | job=%s/%s title=%r company=%r "
                    "h3_count=%s html_preview=%s",
                    idx,
                    total,
                    data["title"],
                    data["company"],
                    len(job.find_all("h3")),
                    self._preview_html(job),
                )

            raw_url = _safe_attr(url_el, "data-url") if url_el else None
            data["url"] = raw_url.split("?lab_feature=")[0] if raw_url else None
            logger.info(
                "Parsed listing fields | job=%s/%s title=%r company=%r raw_url=%r normalized_url=%r",
                idx,
                total,
                data["title"],
                data["company"],
                raw_url,
                data["url"],
            )

            if not data["url"]:
                logger.warning(
                    "Skipping ITViec job because data-url is missing | job=%s/%s title=%r company=%r "
                    "url_element=%s html_preview=%s",
                    idx,
                    total,
                    data["title"],
                    data["company"],
                    self._preview_html(url_el),
                    self._preview_html(job),
                )
                return None, False

            data["logo"] = _safe_attr(_safe_find(company_el, "img"), "data-src")
            data["mode"] = _safe_text(_safe_find(job, "div", class_="text-rich-grey flex-shrink-0"))

            location_el = _safe_find(
                job,
                "div",
                class_="text-rich-grey text-truncate text-nowrap stretched-link position-relative",
            )
            data["location"] = _safe_attr(location_el, "title")

            tag_container = _safe_find(job, "div", class_="imt-4 imb-3 d-flex igap-1")
            if tag_container:
                tags = [_safe_text(a) for a in tag_container.find_all("a") if _safe_text(a)]
                data["tags"] = ", ".join(tags) if tags else None
            self._log_job_state(logging.INFO, "Listing fields after extraction", idx, total, data)

            should_rotate_driver = self._scrape_detail_with_batch_driver(detail_driver, data, idx, total)
        except Exception as e:
            logger.error(
                "Job skipped due to unexpected error | job=%s/%s title=%r company=%r url=%r "
                "error=%s html_preview=%s",
                idx,
                total,
                data.get("title"),
                data.get("company"),
                data.get("url"),
                e,
                self._preview_html(job),
                exc_info=True,
            )

        if data["url"] and data["requirements"] and data["descriptions"]:
            self._log_job_state(logging.INFO, "Job appended", idx, total, data)
            return data, should_rotate_driver

        missing_fields = [field for field in ("url", "requirements", "descriptions") if not data.get(field)]
        logger.warning(
            "Job not appended because required fields are missing | job=%s/%s missing=%s "
            "title=%r company=%r url=%r",
            idx,
            total,
            ", ".join(missing_fields),
            data.get("title"),
            data.get("company"),
            data.get("url"),
        )
        return None, should_rotate_driver

    def _scrape_detail_with_batch_driver(
        self,
        detail_driver: webdriver.Chrome,
        data: Dict[str, Optional[str]],
        idx: int,
        total: int,
    ) -> bool:
        """Load one job detail with the active batch driver and request rotation when retry is needed."""
        try:
            detail_soup = self._load_detail_soup(detail_driver, data["url"])
            self._apply_detail_data(data, detail_soup)

            is_challenge = self._is_challenge_page(detail_soup)
            if is_challenge or not data["descriptions"] or not data["requirements"]:
                logger.warning(
                    "Detail data incomplete, will retry | job=%s/%s title=%r url=%s "
                    "challenge=%s descriptions=%s requirements=%s",
                    idx,
                    total,
                    data["title"],
                    data["url"],
                    is_challenge,
                    bool(data["descriptions"]),
                    bool(data["requirements"]),
                )
                self._retry_detail_with_fresh_driver(data)
                self._log_job_state(logging.INFO, "Detail fields after retry decision", idx, total, data)
                return True

            self._log_job_state(logging.INFO, "Detail fields after extraction", idx, total, data)
            return False
        except Exception as e:
            logger.warning(
                "Primary detail driver failed, will retry with fresh driver | job=%s/%s title=%r url=%s error=%s",
                idx,
                total,
                data["title"],
                data["url"],
                e,
                exc_info=True,
            )
            self._retry_detail_with_fresh_driver(data)
            self._log_job_state(logging.INFO, "Detail fields after retry failure path", idx, total, data)
            return True
        finally:
            time.sleep(random.uniform(ITVIEC_DETAIL_DELAY_MIN_SECONDS, ITVIEC_DETAIL_DELAY_MAX_SECONDS))

    def scrape_jobs(
        self,
        url: str,
        max_jobs: Optional[int] = None,
        max_jobs_page: Optional[int] = None,
    ) -> List[Dict[str, Optional[str]]]:
        """Scrape ITViec jobs from a listing URL.

        Args:
            url: ITViec listing page URL.
            max_jobs: Optional maximum number of listing jobs to process.
            max_jobs_page: Optional maximum number of listing pages to scrape.

        Returns:
            Job records with listing and detail-page fields required by validation.
        """
        logger.info(
            "Starting ITViec scrape | url=%s max_jobs=%s max_jobs_page=%s headless=%s",
            url,
            max_jobs,
            max_jobs_page,
            self.headless,
        )

        discovery_driver = self._init_driver()
        try:
            discovery_soup, _ = self._load_listing_soup(discovery_driver, url)
            total_pages = self._extract_total_pages(discovery_soup)
        finally:
            discovery_driver.quit()

        selected_pages = total_pages if max_jobs_page is None else min(total_pages, max_jobs_page)
        selected_pages = max(1, selected_pages)
        page_urls = [self._listing_page_url(url, page) for page in range(1, selected_pages + 1)]
        logger.info(
            "Discovered ITViec listing pages | url=%s total_pages=%s selected_pages=%s page_urls=%s",
            url,
            total_pages,
            selected_pages,
            page_urls,
        )

        job_data: List[Dict[str, Optional[str]]] = []
        listed_jobs_count = 0
        detail_driver = None
        detail_driver_jobs_processed = 0
        try:
            for page_idx, page_url in enumerate(page_urls, 1):
                remaining_jobs = None if max_jobs is None else max_jobs - listed_jobs_count
                if remaining_jobs is not None and remaining_jobs <= 0:
                    break

                logger.info("Loading ITViec listing page %s/%s | url=%s", page_idx, selected_pages, page_url)
                listing_driver = self._init_driver()
                try:
                    soup, page_source = self._load_listing_soup(listing_driver, page_url)
                    page_jobs = self._select_listing_jobs(soup, page_source, page_url, remaining_jobs)
                finally:
                    self._close_driver(listing_driver, "listing page loaded")

                page_total = len(page_jobs)
                logger.info(
                    "Scraping ITViec detail data for listing page %s/%s | url=%s selected_jobs=%s",
                    page_idx,
                    selected_pages,
                    page_url,
                    page_total,
                )

                for page_job_idx, job in enumerate(page_jobs, 1):
                    if detail_driver is None:
                        detail_driver = self._init_driver()
                        detail_driver_jobs_processed = 0

                    listed_jobs_count += 1
                    data, should_rotate_driver = self._scrape_listing_job(
                        detail_driver,
                        job,
                        page_job_idx,
                        page_total,
                    )
                    detail_driver_jobs_processed += 1
                    if data is not None:
                        job_data.append(data)

                    if should_rotate_driver or detail_driver_jobs_processed >= ITVIEC_DETAIL_DRIVER_JOB_BATCH_SIZE:
                        close_reason = (
                            "detail retry requested"
                            if should_rotate_driver
                            else f"detail batch size reached ({ITVIEC_DETAIL_DRIVER_JOB_BATCH_SIZE})"
                        )
                        self._close_driver(detail_driver, close_reason)
                        detail_driver = None
                        detail_driver_jobs_processed = 0

                logger.info(
                    "Completed ITViec listing page %s/%s | url=%s listed_jobs=%s scraped_jobs=%s",
                    page_idx,
                    selected_pages,
                    page_url,
                    page_total,
                    len(job_data),
                )
        finally:
            if detail_driver is not None:
                self._close_driver(detail_driver, "scrape completed")

        logger.info(
            "ITViec scraping completed | source_url=%s listed_jobs=%s scraped_jobs=%s skipped_jobs=%s",
            url,
            listed_jobs_count,
            len(job_data),
            listed_jobs_count - len(job_data),
        )
        return job_data
