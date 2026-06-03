import logging
import random
import time
from typing import Dict, List, Optional

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
        return webdriver.Chrome(service=Service(self._driver_path), options=self._get_chrome_options())

    def _preview_html(self, element, max_length: int = 500) -> str:
        if element is None:
            return "<None>"

        html = " ".join(str(element).split())
        return html[:max_length] + "..." if len(html) > max_length else html

    def _log_job_state(self, level: int, message: str, idx: int, total: int, data: Dict[str, Optional[str]]) -> None:
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
        try:
            items = section.find_all(["p", "li"], recursive=True)
            texts = [i.get_text() for i in items if i.get_text(strip=True)]
            return " ".join(texts) if texts else None
        except Exception as e:
            logger.warning("Failed to extract text from detail section: %s", e, exc_info=True)
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
        logger.info("Loading ITViec detail page: %s", url)
        driver.get(url)
        try:
            WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.body.innerText.length") > 250)
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
        if not data["url"]:
            logger.warning("Skip detail retry because job URL is missing | title=%r company=%r", data.get("title"), data.get("company"))
            return

        retry_driver = self._init_driver()
        try:
            logger.info("Retrying detail with fresh driver | url=%s title=%r", data["url"], data.get("title"))
            time.sleep(0.5 + random.uniform(0.5, 1.5))
            retry_soup = self._load_detail_soup(retry_driver, data["url"])
            is_challenge = self._is_challenge_page(retry_soup)
            if not is_challenge:
                self._apply_detail_data(data, retry_soup)
            else:
                logger.warning("Retry detail page is still a challenge page | url=%s", data["url"])
        finally:
            retry_driver.quit()

    def scrape_jobs(self, url: str, max_jobs: Optional[int] = None) -> List[Dict[str, Optional[str]]]:
        logger.info("Starting ITViec scrape | url=%s max_jobs=%s headless=%s", url, max_jobs, self.headless)
        driver = self._init_driver()
        driver.get(url)
        time.sleep(3)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        is_listing_challenge = self._is_challenge_page(soup)
        job_candidates = soup.find_all("div", class_="ipy-2")
        jobs = [job for job in job_candidates if job.find("h3", attrs={"data-url": True})]
        filtered_blocks = [job for job in job_candidates if not job.find("h3", attrs={"data-url": True})]
        original_job_count = len(jobs)
        if max_jobs is not None:
            jobs = jobs[:max_jobs]
        driver.quit()

        logger.info(
            "Loaded ITViec listing | url=%s title=%r body_text_len=%s html_len=%s challenge=%s candidate_blocks=%s valid_job_blocks=%s filtered_blocks=%s selected_jobs=%s",
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
        job_data: List[Dict[str, Optional[str]]] = []

        detail_driver = self._init_driver()
        for idx, job in enumerate(jobs, 1):
            logger.info("Processing ITViec listing job %s/%s | html_preview=%s", idx, len(jobs), self._preview_html(job, 350))

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

            try:
                url_el = job.find("h3", attrs={"data-url": True})
                title_el = url_el or _safe_find(job, "h3")
                data["title"] = _safe_text(title_el)
                company_el = _safe_find(job, "div", class_="imy-3 d-flex align-items-center")
                data["company"] = _safe_text(_safe_find(company_el, "span"))

                if url_el is None:
                    logger.warning(
                        "Missing URL element for ITViec job | job=%s/%s title=%r company=%r h3_count=%s html_preview=%s",
                        idx,
                        len(jobs),
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
                    len(jobs),
                    data["title"],
                    data["company"],
                    raw_url,
                    data["url"],
                )

                if not data["url"]:
                    logger.warning(
                        "Skipping ITViec job because data-url is missing | job=%s/%s title=%r company=%r url_element=%s html_preview=%s",
                        idx,
                        len(jobs),
                        data["title"],
                        data["company"],
                        self._preview_html(url_el),
                        self._preview_html(job),
                    )
                    continue

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
                self._log_job_state(logging.INFO, "Listing fields after extraction", idx, len(jobs), data)

                # -------- DETAIL PAGE (NEW DRIVER) -------- #
                if data["url"]:
                    try:
                        detail_soup = self._load_detail_soup(detail_driver, data["url"])
                        self._apply_detail_data(data, detail_soup)

                        is_challenge = self._is_challenge_page(detail_soup)
                        if is_challenge or not data["descriptions"] or not data["requirements"]:
                            logger.warning(
                                "Detail data incomplete, will retry | job=%s/%s title=%r url=%s challenge=%s descriptions=%s requirements=%s",
                                idx,
                                len(jobs),
                                data["title"],
                                data["url"],
                                is_challenge,
                                bool(data["descriptions"]),
                                bool(data["requirements"]),
                            )
                            self._retry_detail_with_fresh_driver(data)
                        self._log_job_state(logging.INFO, "Detail fields after retry decision", idx, len(jobs), data)

                    finally:
                        # detail_driver.quit()
                        detail_driver.delete_all_cookies()
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCache", {})
                        time.sleep(0.5 + random.uniform(0.5, 1.5))
            except Exception as e:
                logger.error(
                    "Job skipped due to unexpected error | job=%s/%s title=%r company=%r url=%r error=%s html_preview=%s",
                    idx,
                    len(jobs),
                    data.get("title"),
                    data.get("company"),
                    data.get("url"),
                    e,
                    self._preview_html(job),
                    exc_info=True,
                )

            if data["url"] and data["requirements"] and data["descriptions"]:
                job_data.append(data)
                self._log_job_state(logging.INFO, "Job appended", idx, len(jobs), data)
            else:
                missing_fields = [
                    field
                    for field in ("url", "requirements", "descriptions")
                    if not data.get(field)
                ]
                logger.warning(
                    "Job not appended because required fields are missing | job=%s/%s missing=%s title=%r company=%r url=%r",
                    idx,
                    len(jobs),
                    ", ".join(missing_fields),
                    data.get("title"),
                    data.get("company"),
                    data.get("url"),
                )
        detail_driver.quit()

        logger.info(
            "ITViec scraping completed | source_url=%s listed_jobs=%s scraped_jobs=%s skipped_jobs=%s",
            url,
            len(jobs),
            len(job_data),
            len(jobs) - len(job_data),
        )
        return job_data
