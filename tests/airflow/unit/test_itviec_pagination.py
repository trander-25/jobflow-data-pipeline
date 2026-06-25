from bs4 import BeautifulSoup
from scripts.crawl_scripts.itviec import ITViecScraper


def test_itviec_extracts_last_pagination_page():
    html = """
    <div class="pagination-search-jobs d-flex justify-content-center ipb-16">
      <nav class="ipagination imt-10">
        <div class="page prev"><a href="/it-jobs/ai-engineer?page=4">prev</a></div>
        <div class="page"><a href="/it-jobs/ai-engineer">1</a></div>
        <div class="page gap">...</div>
        <div class="page"><a href="/it-jobs/ai-engineer?page=4">4</a></div>
        <div class="page current">5</div>
        <div class="page"><a href="/it-jobs/ai-engineer?page=6">6</a></div>
        <div class="page gap">...</div>
        <div class="page"><a href="/it-jobs/ai-engineer?page=9">9</a></div>
        <div class="page next"><a href="/it-jobs/ai-engineer?page=6">next</a></div>
      </nav>
    </div>
    """
    scraper = ITViecScraper.__new__(ITViecScraper)
    soup = BeautifulSoup(html, "html.parser")

    assert scraper._extract_total_pages(soup) == 9


def test_itviec_listing_page_url_replaces_existing_page_param_at_end():
    scraper = ITViecScraper.__new__(ITViecScraper)

    assert (
        scraper._listing_page_url("https://itviec.com/it-jobs/ai-engineer?source=search_job&page=4", 9)
        == "https://itviec.com/it-jobs/ai-engineer?source=search_job&page=9"
    )
