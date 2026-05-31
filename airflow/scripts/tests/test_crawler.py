import pytest

from scripts.crawl_scripts.crawler import Crawler


class DummyITViecScraper:
    def scrape_jobs(self, url, max_jobs=None):
        return [{"source": "itviec", "url": url, "max_jobs": max_jobs}]


class DummyTopCVScraper:
    def scrape_jobs(self, url, max_jobs=None):
        return [{"source": "topcv", "url": url, "max_jobs": max_jobs}]


def test_crawler_dispatches_to_itviec(monkeypatch):
    monkeypatch.setattr("scripts.crawl_scripts.crawler.ITViecScraper", DummyITViecScraper)

    jobs = Crawler("itviec").crawler("https://itviec.com/jobs", max_jobs=2)

    assert jobs == [
        {
            "source": "itviec",
            "url": "https://itviec.com/jobs",
            "max_jobs": 2,
        }
    ]


def test_crawler_dispatches_to_topcv(monkeypatch):
    monkeypatch.setattr("scripts.crawl_scripts.crawler.TopCVScraper", DummyTopCVScraper)

    jobs = Crawler("topcv").crawler("https://www.topcv.vn/jobs", max_jobs=3)

    assert jobs == [
        {
            "source": "topcv",
            "url": "https://www.topcv.vn/jobs",
            "max_jobs": 3,
        }
    ]


def test_crawler_rejects_unsupported_source():
    with pytest.raises(ValueError, match="Unsupported source"):
        Crawler("unknown").crawler("https://example.com")
