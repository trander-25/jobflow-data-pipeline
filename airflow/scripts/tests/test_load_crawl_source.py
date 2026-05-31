import json

from scripts.utils import load_crawl_source


def test_load_crawl_sources_reads_json_from_scripts_directory(tmp_path, monkeypatch):
    scripts_dir = tmp_path / "scripts"
    utils_dir = scripts_dir / "utils"
    utils_dir.mkdir(parents=True)
    config_file = scripts_dir / "source.json"
    expected = [{"source": "topcv", "url": "https://www.topcv.vn"}]
    config_file.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.setattr(load_crawl_source, "__file__", str(utils_dir / "load_crawl_source.py"))

    assert load_crawl_source.load_crawl_sources("source.json") == expected


def test_load_crawl_sources_returns_none_for_missing_file(tmp_path, monkeypatch):
    scripts_dir = tmp_path / "scripts"
    utils_dir = scripts_dir / "utils"
    utils_dir.mkdir(parents=True)
    monkeypatch.setattr(load_crawl_source, "__file__", str(utils_dir / "load_crawl_source.py"))

    assert load_crawl_source.load_crawl_sources("missing.json") is None
