import logging
import random
import time
from typing import Dict, List, Optional

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


class TopCVScraper:
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper with configurable options.

        Args:
            headless: Run Chrome in headless mode
        """
        self.headless = headless
        # Cache driver path on initialization
        logger.info("Initializing ChromeDriver...")
        self._driver_path = ChromeDriverManager().install()

    def _get_chrome_options(self) -> Options:
        """Configure Chrome options."""
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
        """Initialize Chrome WebDriver."""
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
            "%s | job=%s/%s title=%r company=%r url=%r desc=%s req=%s exp=%r edu=%r type_of_work=%r",
            message,
            idx,
            total,
            data.get("title"),
            data.get("company"),
            data.get("url"),
            bool(data.get("descriptions")),
            bool(data.get("requirements")),
            data.get("experience"),
            data.get("education"),
            data.get("type_of_work"),
        )

    def _is_challenge_page(self, soup: BeautifulSoup) -> bool:
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

    def _extract_job_info(self, job) -> tuple:
        """Extract basic job information from job listing."""
        title = _safe_text(_safe_find(job, "h3"))
        company = _safe_text(_safe_find(job, "a", class_="company"))
        img_tag = job.find("img")
        logo = (img_tag.get("src") or img_tag.get("data-src", "")) if img_tag else None
        raw_job_url = _safe_attr(_safe_find(job, "a"), "href")
        job_url = raw_job_url.split("?ta_source")[0] if raw_job_url else None
        location = _safe_text(_safe_find(job.find("label", class_="address"), "span"))
        salary = _safe_text(job.find("label", class_="title-salary") or job.find("label", class_="salary"))
        exp = _safe_text(_safe_find(job.find("label", class_="exp"), "span"))
        return title, company, logo, job_url, location, salary, exp, raw_job_url

    def _parse_brand_job(self, soup) -> tuple:
        """Parse job details from brand job page."""

        def extract_general_info(div):
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

        # Parse descriptions and requirements
        description_box_count = 0
        for div in soup.select("div.premium-job-description__box, div.box-info"):
            description_box_count += 1
            title, content = extract_description_requirement(div)

            if not title:
                continue
            if "Mô tả công việc" == title.get_text(strip=True):
                descriptions = _safe_text(content)
            elif "Yêu cầu ứng viên" == title.get_text(strip=True):
                requirements = _safe_text(content)

            if descriptions and requirements:
                break

        # Parse general info (education, type of work)
        general_info_count = 0
        for div in soup.select("div.general-information-data, div.box-item"):
            general_info_count += 1
            label, value = extract_general_info(div)

            if not label:
                continue
            if label.get_text(strip=True) == "Hình thức làm việc":
                type_of_work = _safe_text(value)
            elif label.get_text(strip=True) == "Học vấn":
                edu = _safe_text(value)

            if type_of_work and edu:
                break

        logger.info(
            "Parsed TopCV brand detail | description_boxes=%s general_info_blocks=%s descriptions=%s requirements=%s edu=%r type_of_work=%r",
            description_box_count,
            general_info_count,
            bool(descriptions),
            bool(requirements),
            edu,
            type_of_work,
        )
        return descriptions, requirements, edu, type_of_work

    def _parse_job_detail(self, soup) -> tuple:
        """Parse job details from standard job page."""

        descriptions = requirements = edu = type_of_work = None

        description_items = soup.select("div.job-description__item")
        for div in description_items:
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

        general_info_blocks = soup.find_all("div", class_="box-general-group-info")
        for div in general_info_blocks:
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

        logger.info(
            "Parsed TopCV standard detail | description_items=%s general_info_blocks=%s descriptions=%s requirements=%s edu=%r type_of_work=%r",
            len(description_items),
            len(general_info_blocks),
            bool(descriptions),
            bool(requirements),
            edu,
            type_of_work,
        )
        return descriptions, requirements, edu, type_of_work

    def scrape_jobs(self, url: str, max_jobs: Optional[int] = None) -> List[Dict[str, str]]:
        """Main method to scrape jobs from TopCV."""
        logger.info("Starting TopCV scrape | url=%s max_jobs=%s headless=%s", url, max_jobs, self.headless)
        # Initialize driver for listing page
        driver = self._init_driver()
        driver.get(url)

        try:
            WebDriverWait(driver, 30).until(lambda d: d.find_elements(By.CSS_SELECTOR, "div.job-item-search-result"))
        except TimeoutException:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            logger.error(
                "Timeout waiting for TopCV listing jobs | url=%s title=%r body_text_len=%s html_len=%s challenge=%s html_preview=%s",
                url,
                soup.title.get_text(strip=True) if soup.title else None,
                len(soup.get_text(" ", strip=True)),
                len(page_source),
                self._is_challenge_page(soup),
                self._preview_html(soup.body),
                exc_info=True,
            )
            driver.quit()
            return []

        time.sleep(0.5 + random.uniform(0.5, 2.5))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        is_listing_challenge = self._is_challenge_page(soup)
        jobs = soup.find_all("div", class_="job-item-search-result")
        original_job_count = len(jobs)
        if max_jobs is not None:
            jobs = jobs[:max_jobs]
        driver.quit()

        logger.info(
            "Loaded TopCV listing | url=%s title=%r body_text_len=%s html_len=%s challenge=%s found_jobs=%s selected_jobs=%s",
            url,
            soup.title.get_text(strip=True) if soup.title else None,
            len(soup.get_text(" ", strip=True)),
            len(page_source),
            is_listing_challenge,
            original_job_count,
            len(jobs),
        )
        if jobs:
            logger.info("First TopCV listing job HTML preview: %s", self._preview_html(jobs[0]))
            logger.info("Last TopCV listing job HTML preview: %s", self._preview_html(jobs[-1]))

        job_data: List[Dict[str, Optional[str]]] = []
        detail_driver = self._init_driver()

        for idx, job in enumerate(jobs, 1):
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
                "job_cat": None,
            }
            try:
                logger.info("Processing TopCV listing job %s/%s | html_preview=%s", idx, len(jobs), self._preview_html(job, 350))

                title, company, logo, job_url, location, salary, exp, raw_job_url = self._extract_job_info(job)
                data["title"] = title
                data["company"] = company
                data["logo"] = logo
                data["url"] = job_url
                data["location"] = location
                data["salary"] = salary
                data["experience"] = exp
                logger.info(
                    "Parsed TopCV listing fields | job=%s/%s title=%r company=%r raw_url=%r normalized_url=%r location=%r salary=%r exp=%r logo=%s",
                    idx,
                    len(jobs),
                    title,
                    company,
                    raw_job_url,
                    job_url,
                    location,
                    salary,
                    exp,
                    bool(logo),
                )

                if not job_url:
                    logger.warning(
                        "Skipping TopCV job detail because URL is missing | job=%s/%s title=%r company=%r html_preview=%s",
                        idx,
                        len(jobs),
                        title,
                        company,
                        self._preview_html(job),
                    )
                    continue

                # Create new driver for each job detail to avoid bot detection
                if job_url:
                    try:
                        logger.info("Loading TopCV detail page | job=%s/%s url=%s", idx, len(jobs), job_url)
                        detail_driver.get(job_url)
                        try:
                            WebDriverWait(detail_driver, 30).until(
                                lambda d: d.execute_script("return document.body.innerText.length") > 250
                            )
                        except TimeoutException:
                            logger.warning(
                                "Timeout waiting for TopCV job details | job=%s/%s title=%r url=%s",
                                idx,
                                len(jobs),
                                title,
                                job_url,
                                exc_info=True,
                            )
                            # detail_driver.quit()
                            time.sleep(0.5 + random.uniform(0.5, 1.5))
                            continue

                        detail_page_source = detail_driver.page_source
                        job_soup = BeautifulSoup(detail_page_source, "html.parser")
                        is_detail_challenge = self._is_challenge_page(job_soup)
                        logger.info(
                            "Loaded TopCV detail page | job=%s/%s url=%s title=%r body_text_len=%s html_len=%s challenge=%s",
                            idx,
                            len(jobs),
                            job_url,
                            job_soup.title.get_text(strip=True) if job_soup.title else None,
                            len(job_soup.get_text(" ", strip=True)),
                            len(detail_page_source),
                            is_detail_challenge,
                        )

                        job_cat_div = job_soup.find("div", string=lambda x: x and "Chuyên môn:" in x)
                        data["job_cat"] = (
                            ", ".join([job_cat.text.strip() for job_cat in job_cat_div.find_next("div").find_all("a")])
                            if job_cat_div
                            else None
                        )

                        if "topcv.vn/brand/" in job_url.strip():
                            detail_type = "brand"
                            descriptions, requirements, edu, type_of_work = self._parse_brand_job(job_soup)
                        elif "topcv.vn/viec-lam/" in job_url.strip():
                            detail_type = "standard"
                            descriptions, requirements, edu, type_of_work = self._parse_job_detail(job_soup)
                        else:
                            detail_type = "unknown"
                            descriptions = requirements = edu = type_of_work = None
                            logger.warning(
                                "Unknown TopCV detail URL pattern | job=%s/%s title=%r url=%s",
                                idx,
                                len(jobs),
                                title,
                                job_url,
                            )

                        data["descriptions"] = descriptions
                        data["requirements"] = requirements
                        data["education"] = edu
                        data["type_of_work"] = type_of_work
                        logger.info(
                            "TopCV detail fields after extraction | job=%s/%s type=%s title=%r job_cat=%r descriptions_len=%s requirements_len=%s edu=%r type_of_work=%r",
                            idx,
                            len(jobs),
                            detail_type,
                            title,
                            data["job_cat"],
                            len(descriptions) if descriptions else 0,
                            len(requirements) if requirements else 0,
                            edu,
                            type_of_work,
                        )
                    finally:
                        detail_driver.delete_all_cookies()
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCache", {})
                        time.sleep(0.5 + random.uniform(0.5, 1.5))
            except Exception as e:
                logger.error(
                    "Error processing TopCV job, skipping | job=%s/%s title=%r company=%r url=%r error=%s html_preview=%s",
                    idx,
                    len(jobs),
                    data.get("title"),
                    data.get("company"),
                    data.get("url"),
                    e,
                    self._preview_html(job),
                    exc_info=True,
                )

            if data["url"] and data["requirements"] and data["descriptions"] and data["experience"]:
                job_data.append(data)
                self._log_job_state(logging.INFO, "TopCV job appended", idx, len(jobs), data)
            else:
                missing_fields = [
                    field
                    for field in ("url", "requirements", "descriptions", "experience")
                    if not data.get(field)
                ]
                logger.warning(
                    "TopCV job not appended because required fields are missing | job=%s/%s missing=%s title=%r company=%r url=%r",
                    idx,
                    len(jobs),
                    ", ".join(missing_fields),
                    data.get("title"),
                    data.get("company"),
                    data.get("url"),
                )

        detail_driver.quit()

        logger.info(
            "TopCV scraping completed | source_url=%s listed_jobs=%s scraped_jobs=%s skipped_jobs=%s",
            url,
            len(jobs),
            len(job_data),
            len(jobs) - len(job_data),
        )
        return job_data
