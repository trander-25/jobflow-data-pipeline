from bot.formatters import format_chat_response, format_jobs_response, split_discord_message


def test_split_discord_message_chunks_long_text():
    chunks = split_discord_message("a" * 2500, limit=1000)

    assert len(chunks) == 3
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_format_jobs_response_includes_job_metadata():
    payload = {
        "retrieved_jobs": [
            {
                "title": "Backend Engineer",
                "company": "JobFlow",
                "locations": "Da Nang",
                "salary": "25-40M",
                "url": "https://example.com/backend",
            }
        ]
    }

    message = format_jobs_response(payload)

    assert "Backend Engineer" in message
    assert "JobFlow" in message
    assert "https://example.com/backend" in message


def test_format_chat_response_does_not_append_sources_section():
    payload = {
        "answer": "1. **Backend Engineer** - JobFlow\nLink: https://example.com/backend",
        "sources": [
            {
                "title": "Backend Engineer",
                "company": "JobFlow",
                "url": "https://example.com/backend",
            }
        ],
    }

    message = format_chat_response(payload)

    assert "Sources:" not in message
    assert message == payload["answer"]
