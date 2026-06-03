from api.services.prompt import build_prompt


def test_prompt_warns_model_when_no_context():
    prompt = build_prompt("Có job Python remote không?", [], [])

    assert "No retrieved jobs." in prompt
    assert "Do not invent company names" in prompt
    assert "Có job Python remote không?" in prompt
