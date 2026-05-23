from pathlib import Path
import time
import random
import sys
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import undetected_chromedriver as uc  # Thay thế webdriver gốc
from helpers.extracting_info import _safe_text, _safe_attr, _safe_find
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# ---------------- LOGGING ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ITViecScraper:
    def __init__(self, headless: bool = False):
        # KHUYÊN DÙNG: Để headless=False ở lần chạy đầu tiên để kiểm tra, 
        # undetected-chromedriver hỗ trợ headless tốt nhất với headless=True (không dùng '--headless=new')
        self.headless = headless

    # ---------------- DRIVER SETUP ---------------- #
    def _init_driver(self) -> uc.Chrome:
        logger.info("Initializing Undetected ChromeDriver...")
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
            
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Không cần add user-agent thủ công vì undetected-chromedriver tự sinh theo chrome hiện tại rất chuẩn
        driver = uc.Chrome(options=options, version_main=148)
        return driver

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
        label = detail_soup.find(
            lambda tag: tag.name in {"div", "span", "p"}
            and tag.get_text(" ", strip=True).rstrip(":").strip().lower() == "job expertise"
        )
        if not label:
            return None

        sibling = label.find_next_sibling()
        if sibling:
            tags = [a.get_text(strip=True) for a in sibling.find_all("a") if a.get_text(strip=True)]
            if 0 < len(tags) <= 10:
                return ", ".join(tags)

        parent = label.parent
        if parent:
            tags = [a.get_text(strip=True) for a in parent.find_all("a") if a.get_text(strip=True)]
            if 0 < len(tags) <= 10:
                return ", ".join(tags)
        return None

    def _extract_by_heading(self, detail_soup: BeautifulSoup, heading_keywords: List[str]) -> Optional[str]:
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

        sections = detail_soup.select("div.imy-5.paragraph")
        if len(sections) >= 2:
            desc = self._extract_text(sections[0])
            req = self._extract_text(sections[1])
            if desc and req and desc == req and len(sections) >= 3:
                alt_req = self._extract_text(sections[2])
                if alt_req and alt_req != desc:
                    req = alt_req
            return desc, req

        desc = self._extract_by_heading(detail_soup, ["job description", "mô tả công việc"])
        req = self._extract_by_heading(
            detail_soup, ["your skills and experience", "requirements", "yêu cầu"]
        )
        return desc, req

    def scrape_jobs(self, url: str, max_jobs: Optional[int] = None) -> List[Dict[str, Optional[str]]]:
        # Khởi tạo driver chính để lấy danh sách job
        main_driver = self._init_driver()
        main_driver.get(url)
        time.sleep(random.uniform(3.0, 5.0)) # Delay ngẫu nhiên một chút

        soup = BeautifulSoup(main_driver.page_source, "html.parser")
        jobs = soup.find_all("div", class_="ipy-2")

        if max_jobs is not None and max_jobs > 0:
            jobs = jobs[:max_jobs]

        logger.info(f"Found {len(jobs)} jobs to process")
        job_data: List[Dict[str, Optional[str]]] = []

        # Tận dụng luôn driver chính này để mở tab con, tránh khởi tạo quá nhiều driver cùng lúc
        for idx, job in enumerate(jobs, 1):
            logger.info(f"Processing job {idx}/{len(jobs)}")

            data = {
                "title": None, "company": None, "logo": None, "url": None,
                "job_cat": None, "location": None, "mode": None, "tags": None,
                "descriptions": None, "requirements": None
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

                # -------- CHI TIẾT JOB (MỞ TAB MỚI) -------- #
                if data["url"]:
                    # Mở một tab mới bằng Javascript
                    main_driver.execute_script(f"window.open('{data['url']}', '_blank');")
                    # Chuyển hướng selenium sang điều khiển tab mới (nằm ở vị trí cuối cùng trong window_handles)
                    main_driver.switch_to.window(main_driver.window_handles[-1])
                    
                    try:
                        # Đợi trang web load xong body text
                        WebDriverWait(main_driver, 20).until(
                            lambda d: d.execute_script("return document.body.innerText.length") > 250
                        )
                        
                        detail_soup = BeautifulSoup(main_driver.page_source, "html.parser")
                        
                        # Nếu dính Cloudflare, đợi thêm một lát xem Turnstile có tự động giải quyết không
                        if self._is_challenge_page(detail_soup):
                            logger.warning(f"Detected Cloudflare challenge for: {data['url']}. Waiting for auto-bypass...")
                            time.sleep(5)
                            detail_soup = BeautifulSoup(main_driver.page_source, "html.parser")

                        data["job_cat"] = self._extract_job_cat(detail_soup)
                        data["descriptions"], data["requirements"] = self._extract_desc_and_req(detail_soup)

                        logger.info(
                            "Detail parse debug - title: %s | Cloudflare Challenge: %s | job_cat: %s | has_desc: %s | has_req: %s",
                            data.get("title"),
                            self._is_challenge_page(detail_soup),
                            data.get("job_cat"),
                            bool(data.get("descriptions")),
                            bool(data.get("requirements")),
                        )

                    except TimeoutException:
                        logger.warning(f"Timeout waiting for job details: {data['url']}")
                    finally:
                        # CÀO XONG THÌ ĐÓNG TAB HIỆN TẠI
                        main_driver.close()
                        # Quay lại tab chính (danh sách job) ban đầu
                        main_driver.switch_to.window(main_driver.window_handles[0])
                        # Nghỉ ngẫu nhiên từ 2-4 giây để giống người thật
                        time.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.error(f"Job skipped due to unexpected error: {e}")
            
            if data["url"]:
                job_data.append(data)
                
        main_driver.quit()
        logger.info(f"Scraping completed. Total jobs scraped: {len(job_data)}")
        return job_data


def main() -> None:
    url = "https://itviec.com/it-jobs/data-scientist"
    max_jobs = 3

    # Gợi ý: Hãy thử để False trước để nhìn trực quan cách nó mở/đóng tab vượt Cloudflare
    scraper = ITViecScraper(headless=False)
    jobs = scraper.scrape_jobs(url=url, max_jobs=max_jobs)

    print(f"\nTotal jobs scraped: {len(jobs)}")
    for idx, job in enumerate(jobs, 1):
        print(f"\nJob {idx}:")
        print(f"Title: {job.get('title')}")
        print(f"Company: {job.get('company')}")
        print(f"Job Category: {job.get('job_cat')}")
        print(f"Description: {str(job.get('descriptions'))[:150]}...")
        print(f"Requirements: {str(job.get('requirements'))[:150]}...")


if __name__ == "__main__":
    main()