from bs4 import BeautifulSoup
from scripts.crawl_scripts.topcv import TopCVScraper


def test_topcv_extracts_total_pages_from_pagination_summary():
    html = """
    <nav class="box-pagination">
      <ul class="pagination">
        <li>
          <span id="job-listing-paginate-text">
            <span class="hight-light">1&nbsp;</span>/&nbsp;200 trang
          </span>
        </li>
      </ul>
    </nav>
    """
    scraper = TopCVScraper.__new__(TopCVScraper)
    soup = BeautifulSoup(html, "html.parser")

    assert scraper._extract_total_pages(soup) == 200


def test_topcv_listing_page_url_replaces_existing_page_param():
    scraper = TopCVScraper.__new__(TopCVScraper)

    assert (
        scraper._listing_page_url("https://www.topcv.vn/tim-viec-lam-sale?page=2&u_sr_id=abc", 9)
        == "https://www.topcv.vn/tim-viec-lam-sale?u_sr_id=abc&page=9"
    )
