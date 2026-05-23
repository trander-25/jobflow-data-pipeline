import time
import random
import logging
import json
import argparse
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from airflow.scripts.crawl_scripts.helpers.extracting_info import (
    _safe_text,
    _safe_attr,
    _safe_find,
)
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
        
        # Thêm các thuộc tính ẩn danh bot mạnh mẽ hơn
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--incognito") # Chạy chế độ ẩn danh mặc định
        
        # Fake User-Agent ngẫu nhiên hoặc chuẩn chỉnh
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        )
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def _init_driver(self) -> webdriver.Chrome:
        logger.info("Initializing ChromeDriver...")
        driver = webdriver.Chrome(
            service=Service(self._driver_path),
            options=self._get_chrome_options()
        )
        # Script này giúp ẩn hoàn toàn thuộc tính navigator.webdriver (bẫy bot phổ biến)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def _extract_text(self, section) -> Optional[str]:
        try:
            items = section.find_all(["p", "li"], recursive=True)
            texts = [i.get_text() for i in items if i.get_text(strip=True)]
            return " ".join(texts) if texts else None
        except Exception:
            return None

    def scrape_jobs(self, url: str, max_jobs: Optional[int] = None) -> List[Dict[str, Optional[str]]]:
        # 1. Thu thập danh sách jobs từ trang tổng quan
        main_driver = self._init_driver()
        main_driver.get(url)
        time.sleep(random.uniform(3.0, 5.0)) # Giãn cách tự nhiên

        soup = BeautifulSoup(main_driver.page_source, "html.parser")
        jobs = soup.find_all("div", class_="ipy-2")
        if max_jobs is not None:
            jobs = jobs[:max_jobs]
        main_driver.quit()

        logger.info(f"Found {len(jobs)} jobs")
        job_data: List[Dict[str, Optional[str]]] = []

        # 2. Đi vào chi tiết từng job
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

                data["title"] = _safe_text(_safe_find(job, "h3"))
                company_el = _safe_find(job, "div", class_="imy-3 d-flex align-items-center")
                data["company"] = _safe_text(_safe_find(company_el, "span"))
                data["logo"] = _safe_attr(_safe_find(company_el, "img"), "data-src")
                data["mode"] = _safe_text(_safe_find(job, "div", class_="text-rich-grey flex-shrink-0"))

                location_el = _safe_find(job, "div", class_="text-rich-grey text-truncate text-nowrap stretched-link position-relative")
                data["location"] = _safe_attr(location_el, "title")

                tag_container = _safe_find(job, "div", class_="imt-4 imb-3 d-flex igap-1")
                if tag_container:
                    tags = [_safe_text(a) for a in tag_container.find_all("a") if _safe_text(a)]
                    data["tags"] = ", ".join(tags) if tags else None

                # -------- DETAIL PAGE (Khởi tạo riêng lẻ để reset Session hoàn toàn) -------- #
                if data["url"]:
                    detail_driver = None
                    try:
                        detail_driver = self._init_driver()
                        detail_driver.get(data["url"])
                        
                        # Chờ đợi thông minh dựa vào class đặc trưng của phần nội dung thay vì đếm ký tự chung chung
                        WebDriverWait(detail_driver, 15).until(
                            lambda d: d.find_element("class name", "paragraph")
                        )
                        
                        # Nghỉ ngơi ngẫu nhiên giống hành vi người thật đọc trang
                        time.sleep(random.uniform(1.5, 3.5))

                        detail_soup = BeautifulSoup(detail_driver.page_source, "html.parser")

                        # Parse Job Category
                        job_cat_div = detail_soup.find("div", string="Job Expertise:")
                        data["job_cat"] = ", ".join([job_cat.text.strip() for job_cat in job_cat_div.find_next("div").find_all("a")]) if job_cat_div else None

                        # Parse Content Sections
                        sections = detail_soup.find_all("div", class_="imy-5 paragraph")
                        if len(sections) > 0:
                            data["descriptions"] = self._extract_text(sections[0])
                        if len(sections) > 1:
                            data["requirements"] = self._extract_text(sections[1])

                    except TimeoutException:
                        logger.warning(f"Timeout hoặc bị Block khi tải chi tiết URL: {data['url']}")
                    except Exception as e:
                        logger.error(f"Lỗi khi cào trang chi tiết: {e}")
                    finally:
                        if detail_driver:
                            detail_driver.quit() # Tắt hẳn browser để xóa sạch dấu vết

                # Nghỉ một nhịp trước khi sang job tiếp theo
                time.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.error(f"Job skipped due to unexpected error: {e}")
            
            if data["url"] and data["title"] and data["company"]:
                job_data.append(data)
                
        logger.info(f"Scraping completed. Total jobs scraped: {len(job_data)}")
        return job_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ITViec scraper test.")
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=2,
        help="Maximum number of listing jobs to process before scraping details.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://itviec.com/it-jobs/data-scientist",
        help="Target ITViec URL for testing.",
    )
    args = parser.parse_args()

    scraper = ITViecScraper(headless=True)
    jobs = scraper.scrape_jobs(args.url, max_jobs=args.max_jobs)

    print(f"Total jobs scraped (valid): {len(jobs)}")
    print(json.dumps(jobs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
