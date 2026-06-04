from api.services.chroma_store import map_chroma_results, source_links


def test_map_chroma_results_to_job_sources():
    result = {
        "ids": [["job-1"]],
        "documents": [["Job Title: Data Engineer. Company: JobFlow."]],
        "metadatas": [
            [
                {
                    "job_title": "Data Engineer",
                    "company_name": "JobFlow",
                    "source_platform": "topcv",
                    "url": "https://example.com/job-1",
                    "job_locations": "Ho Chi Minh",
                    "salary": "30-50M",
                }
            ]
        ],
        "distances": [[0.12]],
    }

    jobs = map_chroma_results(result)

    assert len(jobs) == 1
    assert jobs[0].job_id == "job-1"
    assert jobs[0].title == "Data Engineer"
    assert jobs[0].company == "JobFlow"
    assert jobs[0].url == "https://example.com/job-1"
    assert jobs[0].distance == 0.12
    assert source_links(jobs)[0].title == "Data Engineer"
