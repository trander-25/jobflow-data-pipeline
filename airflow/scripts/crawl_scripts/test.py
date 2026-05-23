from pathlib import Path
import time
import random
import sys
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

# REPO_ROOT = Path(__file__).resolve().parents[2]
# if str(REPO_ROOT) not in sys.path:
#     sys.path.insert(0, str(REPO_ROOT))
# from helpers.extracting_info import _safe_text, _safe_attr, _safe_find

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
        # Increase waits to reduce flaky detail extraction on slower/challenged pages.
        self.detail_wait_timeout = 45
        self.detail_retry_sleep = (4.0, 5.0)
        self.detail_between_jobs_sleep = (1.5, 3.0)

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

    def _is_challenge_page(self, detail_soup: BeautifulSoup) -> bool:
        title_text = (detail_soup.title.get_text(strip=True) if detail_soup.title else "").lower()
        body_text = detail_soup.get_text(" ", strip=True).lower()
        challenge_signals = [
            "just a moment",
            "attention required",
            "verify you are human",
            "cf-challenge",
            "cloudflare",
        ]
        return any(sig in title_text or sig in body_text for sig in challenge_signals)

    def _extract_job_cat(self, detail_soup: BeautifulSoup) -> Optional[str]:
        # Match strict label text to avoid grabbing huge unrelated containers.
        label = detail_soup.find(
            lambda tag: tag.name in {"div", "span", "p"}
            and tag.get_text(" ", strip=True).rstrip(":").strip().lower() == "job expertise"
        )
        if not label:
            return None

        # Try sibling first (most common structure on detail pages).
        sibling = label.find_next_sibling()
        if sibling:
            tags = [a.get_text(strip=True) for a in sibling.find_all("a") if a.get_text(strip=True)]
            if 0 < len(tags) <= 10:
                return ", ".join(tags)

        # Then try within parent, but keep only small/local tag groups.
        parent = label.parent
        if parent:
            tags = [a.get_text(strip=True) for a in parent.find_all("a") if a.get_text(strip=True)]
            if 0 < len(tags) <= 10:
                return ", ".join(tags)
        return None

    def _extract_by_heading(self, detail_soup: BeautifulSoup, heading_keywords: List[str]) -> Optional[str]:
        # Parse by semantic heading instead of relying on fixed section index.
        headings = detail_soup.find_all(["h2", "h3", "h4", "div", "span"])
        for h in headings:
            heading_text = h.get_text(" ", strip=True).lower()
            if not heading_text:
                continue
            if not any(k in heading_text for k in heading_keywords):
                continue

            for sib in h.find_all_next():
                if sib is h:
                    continue
                if sib.name in {"h2", "h3", "h4"}:
                    break
                classes = sib.get("class", [])
                if "paragraph" in classes:
                    extracted = self._extract_text(sib)
                    if extracted:
                        return extracted
        return None

    def _extract_desc_and_req(self, detail_soup: BeautifulSoup):
        desc = None
        req = None

        # Primary strategy: ITviec detail blocks usually expose these sections in order.
        sections = detail_soup.select("div.imy-5.paragraph")
        if len(sections) >= 2:
            desc = self._extract_text(sections[0])
            req = self._extract_text(sections[1])
            # Some pages can duplicate section content; try next block as fallback.
            if desc and req and desc == req and len(sections) >= 3:
                alt_req = self._extract_text(sections[2])
                if alt_req and alt_req != desc:
                    req = alt_req
            return desc, req

        # Fallback strategy: semantic heading matching.
        desc = self._extract_by_heading(detail_soup, ["job description", "mô tả công việc"])
        req = self._extract_by_heading(
            detail_soup, ["your skills and experience", "requirements", "yêu cầu"]
        )
        return desc, req

    def _load_detail_once(self, driver: webdriver.Chrome, url: str) -> BeautifulSoup:
        driver.get(url)
        try:
            WebDriverWait(driver, self.detail_wait_timeout).until(
                lambda d: d.execute_script("return document.body.innerText.length") > 250
            )
        except TimeoutException:
            logger.warning(f"Timeout waiting for job details to load for URL: {url}")
        return BeautifulSoup(driver.page_source, "html.parser")

    def scrape_jobs(
        self, url: str, max_jobs: Optional[int] = None
    ) -> List[Dict[str, Optional[str]]]:
        driver = self._init_driver()
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        jobs = soup.find_all("div", class_="ipy-2")
        driver.quit()

        if max_jobs is not None and max_jobs > 0:
            jobs = jobs[:max_jobs]

        logger.info(f"Found {len(jobs)} jobs to process")
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
                        # OLD FLOW (single detail_driver for all jobs):
                        detail_driver.get(data["url"])
                        #
                        # NEW FLOW:
                        # Re-create driver at job 2 to reduce risk of challenge
                        # tied to the current session/fingerprint.
                        # if idx == 2:
                        #     logger.info("Reinitializing detail driver at job 2 to avoid challenge carry-over")
                        #     try:
                        #         detail_driver.quit()
                        #     except Exception:
                        #         pass
                        #     detail_driver = self._init_driver()

                        detail_soup = self._load_detail_once(detail_driver, data["url"])
                        if self._is_challenge_page(detail_soup):
                            logger.warning(f"Possible anti-bot/challenge page for URL: {data['url']}. Retrying once...")
                            time.sleep(random.uniform(*self.detail_retry_sleep))
                            detail_driver.get(data["url"])
                            time.sleep(random.uniform(*self.detail_retry_sleep))
                            detail_soup = BeautifulSoup(detail_driver.page_source, "html.parser")

                        data["job_cat"] = self._extract_job_cat(detail_soup)
                        data["descriptions"], data["requirements"] = self._extract_desc_and_req(detail_soup)

                        # If detail is still empty, retry this specific job with a fresh one-off driver.
                        needs_fresh_retry = (
                            self._is_challenge_page(detail_soup)
                            or not data["job_cat"]
                            or not data["descriptions"]
                            or not data["requirements"]
                        )
                        if needs_fresh_retry:
                            logger.info(
                                "Retrying job with fresh isolated driver - title: %s",
                                data.get("title"),
                            )
                            isolated_driver = self._init_driver()
                            try:
                                time.sleep(random.uniform(*self.detail_retry_sleep))
                                isolated_soup = self._load_detail_once(isolated_driver, data["url"])
                                if self._is_challenge_page(isolated_soup):
                                    logger.warning(
                                        f"Fresh driver still challenged for URL: {data['url']}"
                                    )
                                else:
                                    # Replace only when new parse gives values.
                                    fresh_job_cat = self._extract_job_cat(isolated_soup)
                                    fresh_desc, fresh_req = self._extract_desc_and_req(isolated_soup)
                                    if fresh_job_cat:
                                        data["job_cat"] = fresh_job_cat
                                    if fresh_desc:
                                        data["descriptions"] = fresh_desc
                                    if fresh_req:
                                        data["requirements"] = fresh_req
                            finally:
                                isolated_driver.quit()

                        logger.info(
                            "Detail parse debug - title: %s | challenge: %s | job_cat: %s | has_desc: %s | has_req: %s",
                            data.get("title"),
                            self._is_challenge_page(detail_soup),
                            data.get("job_cat"),
                            bool(data.get("descriptions")),
                            bool(data.get("requirements")),
                        )

                    finally:
                        # OLD FLOW (do not quit here, reuse one driver):
                        # detail_driver.quit()
                        detail_driver.delete_all_cookies()
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
                        detail_driver.execute_cdp_cmd("Network.clearBrowserCache", {})
                        time.sleep(random.uniform(*self.detail_between_jobs_sleep))
            except Exception as e:
                logger.error(f"Job skipped due to unexpected error: {e}")
            
            if data["url"]:
                job_data.append(data)
        detail_driver.quit()
        
        logger.info(f"Scraping completed. Total jobs scraped: {len(job_data)}")
        return job_data


def main() -> None:
    url = "https://itviec.com/it-jobs/ai-engineer"
    max_jobs = 10

    scraper = ITViecScraper(headless=True)
    jobs = scraper.scrape_jobs(url=url, max_jobs=max_jobs)

    print(f"Total jobs scraped: {len(jobs)}")
    for idx, job in enumerate(jobs, 1):
        print(f"\nJob {idx}:")
        print(f"Title: {job.get('title')}")
        print(f"Company: {job.get('company')}")
        print(f"URL: {job.get('url')}")
        print(f"Location: {job.get('location')}")
        print(f"Mode: {job.get('mode')}")
        print(f"Job Category: {job.get('job_cat')}")
        print(f"Tags: {job.get('tags')}")
        print(f"Description: {job.get('descriptions')}")
        print(f"Requirements: {job.get('requirements')}")


if __name__ == "__main__":
    main()
