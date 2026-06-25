import logging
import random
import re
import time
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .helpers.extracting_info import _safe_attr, _safe_find, _safe_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ---------------- SCRAPER SETTINGS ---------------- #
TOPCV_LISTING_WAIT_TIMEOUT_SECONDS = 30
TOPCV_LISTING_DELAY_MIN_SECONDS = 0.5
TOPCV_LISTING_DELAY_MAX_SECONDS = 3.0
TOPCV_DETAIL_WAIT_TIMEOUT_SECONDS = 30
TOPCV_DETAIL_MIN_BODY_TEXT_LENGTH = 250
TOPCV_DETAIL_DRIVER_JOB_BATCH_SIZE = 10
TOPCV_DETAIL_DELAY_MIN_SECONDS = 1
TOPCV_DETAIL_DELAY_MAX_SECONDS = 4
TOPCV_RETRY_DELAY_MIN_SECONDS = 2
TOPCV_RETRY_DELAY_MAX_SECONDS = 4


class TopCVScraper:
    """Scrape TopCV listing pages and enrich records from job detail pages."""

    def __init__(self, headless: bool = True):
        """Initialize scraper options and resolve the ChromeDriver path.

        Args:
            headless: Whether Chrome should run without a visible browser window.
        """
        self.headless = headless
        # Cache the driver path once so each task does not resolve it repeatedly.
        logger.info("Initializing ChromeDriver...")
        self._driver_path = ChromeDriverManager().install()

    def _get_chrome_options(self) -> Options:
        """Build Chrome options used by the TopCV Selenium driver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        )
        return chrome_options

    def _init_driver(self) -> webdriver.Chrome:
        """Create a Selenium Chrome driver for TopCV pages."""
        logger.info("Initializing ChromeDriver...")
        return webdriver.Chrome(service=Service(self._driver_path), options=self._get_chrome_options())

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

    def _listing_page_url(self, url: str, page: int) -> str:
        """Return a TopCV listing URL with the requested page query parameter."""
        parsed_url = urlparse(url)
        query_params = [
            (key, value)
            for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if key != "page"
        ]
        query_params.append(("page", str(page)))
        return urlunparse(parsed_url._replace(query=urlencode(query_params)))

    def _extract_total_pages(self, soup: BeautifulSoup) -> int:
        """Extract TopCV total listing pages from the pagination summary."""
        paginate_text = _safe_text(soup.select_one("#job-listing-paginate-text"))
        match = re.search(r"/\s*([\d.]+)\s*trang", paginate_text)
        if not match:
            return 1
        return int(match.group(1).replace(".", ""))

    def _load_listing_soup(self, driver: webdriver.Chrome, url: str) -> tuple[BeautifulSoup, str]:
        """Load one TopCV listing page and parse it into BeautifulSoup."""
        driver.get(url)
        try:
            WebDriverWait(driver, TOPCV_LISTING_WAIT_TIMEOUT_SECONDS).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "div.job-item-search-result")
            )
        except TimeoutException:
            logger.warning("Timeout waiting for TopCV listing jobs to load for URL: %s", url)

        time.sleep(random.uniform(TOPCV_LISTING_DELAY_MIN_SECONDS, TOPCV_LISTING_DELAY_MAX_SECONDS))
        page_source = driver.page_source
        return BeautifulSoup(page_source, "html.parser"), page_source

    def _select_listing_jobs(
        self,
        soup: BeautifulSoup,
        page_source: str,
        url: str,
        remaining_jobs: Optional[int],
    ) -> List:
        """Select valid TopCV listing job cards from one page."""
        is_challenge = self._is_challenge_page(soup)
        jobs = soup.find_all("div", class_="job-item-search-result")
        original_job_count = len(jobs)
        if remaining_jobs is not None:
            jobs = jobs[:remaining_jobs]

        logger.info(
            "Loaded TopCV listing | url=%s title=%r body_text_len=%s html_len=%s challenge=%s "
            "valid_job_blocks=%s selected_jobs=%s",
            url,
            soup.title.get_text(strip=True) if soup.title else None,
            len(soup.get_text(" ", strip=True)),
            len(page_source),
            is_challenge,
            original_job_count,
            len(jobs),
        )
        return jobs

    def _is_challenge_page(self, soup: BeautifulSoup) -> bool:
        """Detect captcha or bot-protection challenge pages."""
        title_text = (soup.title.get_text(strip=True) if soup.title else "").lower()
        body_text = soup.get_text(" ", strip=True).lower()
        challenge_signals = [
            "access denied",
            "captcha",
            "checking your browser",
            "just a moment",
            "verify you are human",
            "cloudflare",
        ]
        return any(signal in title_text or signal in body_text for signal in challenge_signals)

    def _load_detail_soup(self, driver: webdriver.Chrome, url: str, idx: int, total: int) -> Optional[BeautifulSoup]:
        """Load one TopCV detail page and parse it into BeautifulSoup."""
        logger.info("Loading TopCV detail page | job=%s/%s url=%s", idx, total, url)
        try:
            driver.get(url)
            WebDriverWait(driver, TOPCV_DETAIL_WAIT_TIMEOUT_SECONDS).until(
                lambda d: d.execute_script("return document.body.innerText.length")
                > TOPCV_DETAIL_MIN_BODY_TEXT_LENGTH
            )
        except TimeoutException:
            logger.warning("Timeout waiting for job details to load for URL: %s", url)
        except Exception as e:
            logger.warning("Error loading URL %s: %s", url, e)

        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            return soup
        except Exception as e:
            logger.error("Failed to get page source or parse soup for URL %s: %s", url, e)
            return None

    def _apply_detail_data(self, data: Dict[str, Optional[str]], job_soup: BeautifulSoup) -> None:
        """Populate detail fields from either a brand page or a standard job page."""
        job_url = data["url"] or ""
        job_cat_div = job_soup.find("div", string=lambda x: x and "Chuyên môn:" in x)
        data["job_cat"] = (
            ", ".join([job_cat.text.strip() for job_cat in job_cat_div.find_next("div").find_all("a")])
            if job_cat_div
            else None
        )

        if "topcv.vn/brand/" in job_url.strip():
            descriptions, requirements, edu, type_of_work = self._parse_brand_job(job_soup)
        elif "topcv.vn/viec-lam/" in job_url.strip():
            descriptions, requirements, edu, type_of_work = self._parse_job_detail(job_soup)
        else:
            descriptions = requirements = edu = type_of_work = None

        data["descriptions"] = descriptions
        data["requirements"] = requirements
        data["education"] = edu
        data["type_of_work"] = type_of_work

    def _extract_job_info(self, job) -> tuple:
        """Extract basic fields from one TopCV listing card."""
        title = _safe_text(_safe_find(job, "h3"))
        company = _safe_text(_safe_find(job, "a", class_="company"))
        img_tag = job.find("img")
        logo = img_tag.get("src") or img_tag.get("data-src", "")
        job_url = _safe_attr(_safe_find(job, "a"), "href").split("?ta_source")[0]
        location = _safe_text(_safe_find(job.find("label", class_="address"), "span"))
        salary = _safe_text(job.find("label", class_="title-salary") or job.find("label", class_="salary"))
        exp = _safe_text(_safe_find(job.find("label", class_="exp"), "span"))
        return title, company, logo, job_url, location, salary, exp

    def _parse_brand_job(self, soup) -> tuple:
        """Parse descriptions, requirements, education, and work type from a TopCV brand page."""

        def extract_general_info(div):
            """Extract label and value elements from a brand-page general-info block."""
            label = div.select_one(".general-information-data__label")
            value = div.select_one(".general-information-data__value")
            if label and value:
                return label, value

            label = div.find("strong")
            value = div.find("span")
            if label and value:
                return label, value

            return None, None

        def extract_description_requirement(div):
            """Extract title and content elements from a brand-page description block."""
            h2 = div.select_one("h2.premium-job-description__box--title")
            content_div = div.select_one("div.premium-job-description__box--content")
            content = content_div if content_div else None
            if h2 and content:
                return h2, content

            h2 = div.select_one("h2.title")
            content_div = div.select_one("div.content-tab")
            content = content_div if content_div else None
            if h2 and content:
                return h2, content

            return None, None

        descriptions = requirements = edu = type_of_work = None

        # Parse description and requirement blocks.
        for div in soup.select("div.premium-job-description__box, div.box-info"):
            title, content = extract_description_requirement(div)

            if not title:
                continue
            if "Mô tả công việc" == title.get_text(strip=True):
                descriptions = _safe_text(content)
            elif "Yêu cầu ứng viên" == title.get_text(strip=True):
                requirements = _safe_text(content)

            if descriptions and requirements:
                break

        # Parse general information such as education and work type.
        for div in soup.select("div.general-information-data, div.box-item"):
            label, value = extract_general_info(div)

            if not label:
                continue
            if label.get_text(strip=True) == "Hình thức làm việc":
                type_of_work = _safe_text(value)
            elif label.get_text(strip=True) == "Học vấn":
                edu = _safe_text(value)

            if type_of_work and edu:
                break

        return descriptions, requirements, edu, type_of_work

    def _parse_job_detail(self, soup) -> tuple:
        """Parse descriptions, requirements, education, and work type from a standard TopCV job page."""

        descriptions = requirements = edu = type_of_work = None

        for div in soup.select("div.job-description__item"):
            h3 = _safe_find(div, "h3")
            content = _safe_find(div, "div", "job-description__item--content")

            if not h3:
                continue

            title = h3.get_text(strip=True)

            if title == "Mô tả công việc":
                descriptions = _safe_text(content)

            elif title == "Yêu cầu ứng viên":
                requirements = _safe_text(content)

            if descriptions and requirements:
                break

        for div in soup.find_all("div", class_="box-general-group-info"):
            title_div = _safe_find(div, "div", "box-general-group-info-title")
            value_div = _safe_find(div, "div", "box-general-group-info-value")
            if not title_div:
                continue

            label = title_div.get_text(strip=True)
            value = _safe_text(value_div)
            if label == "Hình thức làm việc":
                type_of_work = value
            elif label == "Học vấn":
                edu = value

            if type_of_work and edu:
                break

        return descriptions, requirements, edu, type_of_work

    def _retry_detail_with_fresh_driver(self, data: Dict[str, Optional[str]], idx: int, total: int) -> None:
        """Retry detail extraction with a fresh driver when the active session is blocked."""
        if not data["url"]:
            logger.warning("Skip detail retry because job URL is missing | title=%r", data.get("title"))
            return

        retry_driver = self._init_driver()
        try:
            logger.info("Retrying TopCV detail with fresh driver | job=%s/%s url=%s", idx, total, data["url"])
            time.sleep(random.uniform(TOPCV_RETRY_DELAY_MIN_SECONDS, TOPCV_RETRY_DELAY_MAX_SECONDS))
            retry_soup = self._load_detail_soup(retry_driver, data["url"], idx, total)
            if retry_soup is not None and not self._is_challenge_page(retry_soup):
                self._apply_detail_data(data, retry_soup)
            else:
                logger.warning("Retry detail page is still a challenge or empty page | url=%s", data["url"])
        finally:
            self._close_driver(retry_driver, "topcv detail retry completed")

    def _scrape_detail_with_batch_driver(
        self,
        detail_driver: webdriver.Chrome,
        data: Dict[str, Optional[str]],
        idx: int,
        total: int,
    ) -> bool:
        """Load one TopCV detail with the active batch driver and request rotation when retry is needed."""
        try:
            job_soup = self._load_detail_soup(detail_driver, data["url"], idx, total)
            is_challenge = job_soup is None or self._is_challenge_page(job_soup)
            if not is_challenge:
                self._apply_detail_data(data, job_soup)

            if is_challenge or not data["descriptions"] or not data["requirements"]:
                logger.warning(
                    "TopCV detail incomplete, will retry | job=%s/%s title=%r url=%s challenge=%s "
                    "descriptions=%s requirements=%s",
                    idx,
                    total,
                    data["title"],
                    data["url"],
                    is_challenge,
                    bool(data["descriptions"]),
                    bool(data["requirements"]),
                )
                self._retry_detail_with_fresh_driver(data, idx, total)
                return True

            logger.info(
                "TopCV detail fields extracted | job=%s/%s title=%r url=%s descriptions_len=%s requirements_len=%s",
                idx,
                total,
                data["title"],
                data["url"],
                len(data["descriptions"]) if data["descriptions"] else 0,
                len(data["requirements"]) if data["requirements"] else 0,
            )
            return False
        except Exception as e:
            logger.warning(
                "Primary TopCV detail driver failed, will retry with fresh driver | job=%s/%s title=%r url=%s error=%s",
                idx,
                total,
                data["title"],
                data["url"],
                e,
                exc_info=True,
            )
            self._retry_detail_with_fresh_driver(data, idx, total)
            return True
        finally:
            time.sleep(random.uniform(TOPCV_DETAIL_DELAY_MIN_SECONDS, TOPCV_DETAIL_DELAY_MAX_SECONDS))

    def _scrape_listing_job(
        self,
        detail_driver: webdriver.Chrome,
        job,
        idx: int,
        total: int,
    ) -> tuple[Optional[Dict[str, Optional[str]]], bool]:
        """Extract one TopCV listing job and enrich it from its detail page."""
        data = {
            "title": None,
            "company": None,
            "logo": None,
            "url": None,
            "location": None,
            "salary": None,
            "descriptions": None,
            "requirements": None,
            "experience": None,
            "education": None,
            "type_of_work": None,
        }
        should_rotate_driver = False

        try:
            logger.info("Processing TopCV job %s/%s", idx, total)
            title, company, logo, job_url, location, salary, exp = self._extract_job_info(job)
            data["title"] = title
            data["company"] = company
            data["logo"] = logo
            data["url"] = job_url
            data["location"] = location
            data["salary"] = salary
            data["experience"] = exp

            if data["url"]:
                should_rotate_driver = self._scrape_detail_with_batch_driver(detail_driver, data, idx, total)
        except Exception as e:
            logger.error("Error processing TopCV job %s/%s, skipping... %s", idx, total, e, exc_info=True)

        if data["url"] and data["requirements"] and data["descriptions"] and data["experience"]:
            logger.info("TopCV job appended successfully: %s", data["title"])
            return data, should_rotate_driver

        missing = [key for key in ["url", "requirements", "descriptions", "experience"] if not data.get(key)]
        logger.warning(
            "TopCV job NOT appended because of missing fields: %s | title=%r company=%r url=%r",
            missing,
            data.get("title"),
            data.get("company"),
            data.get("url"),
        )
        return None, should_rotate_driver

    def scrape_jobs(
        self,
        url: str,
        max_jobs: Optional[int] = None,
        max_jobs_page: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Scrape TopCV jobs from a listing URL.

        Args:
            url: TopCV listing page URL.
            max_jobs: Optional maximum number of listing jobs to process.
            max_jobs_page: Optional maximum number of listing pages to scrape.

        Returns:
            Job records with listing and detail-page fields required by validation.
        """
        discovery_driver = self._init_driver()
        try:
            discovery_soup, _ = self._load_listing_soup(discovery_driver, url)
            total_pages = self._extract_total_pages(discovery_soup)
        finally:
            self._close_driver(discovery_driver, "topcv pagination discovered")

        selected_pages = total_pages if max_jobs_page is None else min(total_pages, max_jobs_page)
        selected_pages = max(1, selected_pages)
        page_urls = [self._listing_page_url(url, page) for page in range(1, selected_pages + 1)]
        logger.info(
            "Discovered TopCV listing pages | url=%s total_pages=%s selected_pages=%s page_urls=%s",
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

                listing_driver = self._init_driver()
                try:
                    soup, page_source = self._load_listing_soup(listing_driver, page_url)
                    page_jobs = self._select_listing_jobs(soup, page_source, page_url, remaining_jobs)
                finally:
                    self._close_driver(listing_driver, "topcv listing page loaded")

                page_total = len(page_jobs)
                logger.info(
                    "Scraping TopCV detail data for listing page %s/%s | url=%s selected_jobs=%s",
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

                    if should_rotate_driver or detail_driver_jobs_processed >= TOPCV_DETAIL_DRIVER_JOB_BATCH_SIZE:
                        close_reason = (
                            "topcv detail retry requested"
                            if should_rotate_driver
                            else f"topcv detail batch size reached ({TOPCV_DETAIL_DRIVER_JOB_BATCH_SIZE})"
                        )
                        self._close_driver(detail_driver, close_reason)
                        detail_driver = None
                        detail_driver_jobs_processed = 0

                logger.info(
                    "Completed TopCV listing page %s/%s | url=%s listed_jobs=%s scraped_jobs=%s",
                    page_idx,
                    selected_pages,
                    page_url,
                    page_total,
                    len(job_data),
                )
        finally:
            if detail_driver is not None:
                self._close_driver(detail_driver, "topcv scrape completed")

        logger.info("TopCV scraping completed. Total jobs scraped: %s", len(job_data))
        return job_data
