import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scraper tests from one entrypoint.")
    parser.add_argument(
        "--source",
        choices=["itviec", "topcv"],
        default="itviec",
        help="Which scraper test to run.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Override target URL. If omitted, uses source default URL.",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=2,
        help="Maximum number of listing jobs to process before scraping details.",
    )
    args = parser.parse_args()

    if args.source == "itviec":
        from airflow.scripts.crawl_scripts.itviec_test import ITViecScraper

        url = args.url or "https://itviec.com/it-jobs/data-scientist"
        scraper = ITViecScraper(headless=True)
        jobs = scraper.scrape_jobs(url, max_jobs=args.max_jobs)
    else:
        from airflow.scripts.crawl_scripts.topcv_test import TopCVScraper

        url = args.url or "https://www.topcv.vn/tim-viec-lam-ai-engineer"
        scraper = TopCVScraper(headless=True)
        jobs = scraper.scrape_jobs(url, max_jobs=args.max_jobs)

    print(f"Total jobs scraped (valid): {len(jobs)}")


if __name__ == "__main__":
    main()
