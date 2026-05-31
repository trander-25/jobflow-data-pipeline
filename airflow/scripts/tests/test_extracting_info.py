from bs4 import BeautifulSoup

from scripts.crawl_scripts.helpers.extracting_info import _safe_attr, _safe_find, _safe_text


def test_safe_text_returns_stripped_text():
    soup = BeautifulSoup("<div>  Data Engineer  </div>", "html.parser")

    assert _safe_text(soup.div) == "Data Engineer"


def test_safe_text_returns_none_for_missing_element():
    assert _safe_text(None) is None


def test_safe_attr_returns_attribute_value():
    soup = BeautifulSoup('<a href="https://example.com/job">Job</a>', "html.parser")

    assert _safe_attr(soup.a, "href") == "https://example.com/job"


def test_safe_attr_returns_none_for_missing_attribute():
    soup = BeautifulSoup("<a>Job</a>", "html.parser")

    assert _safe_attr(soup.a, "href") is None


def test_safe_find_returns_matching_child():
    soup = BeautifulSoup('<section><span class="salary">$1000</span></section>', "html.parser")

    result = _safe_find(soup.section, "span", class_="salary")

    assert result.get_text(strip=True) == "$1000"


def test_safe_find_returns_none_for_missing_parent():
    assert _safe_find(None, "span") is None
