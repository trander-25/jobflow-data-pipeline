from api.config import Settings
from api.main import app, chat
from api.schemas import ChatRequest, JobSource


class FakeJobStore:
    def search(self, query, top_k):
        assert query == "Tìm job Data Engineer"
        assert top_k == 3
        return [
            JobSource(
                job_id="job-1",
                title="Data Engineer",
                company="JobFlow",
                url="https://example.com/job-1",
                locations="Ho Chi Minh",
                salary="30-50M",
                document="Data engineering role",
            )
        ]


class FakeHistoryStore:
    def __init__(self):
        self.added = []

    def recent_messages(self, user_id, limit):
        assert user_id == "discord-user"
        assert limit == 6
        return [{"role": "user", "message": "Xin chào"}]

    def add_message(self, user_id, role, message):
        self.added.append((user_id, role, message))


class FakeLlm:
    def generate(self, prompt):
        assert "Retrieved job context" in prompt
        return "Có 1 job Data Engineer phù hợp: https://example.com/job-1"


def test_chat_endpoint_uses_retrieval_llm_and_history():
    history = FakeHistoryStore()
    app.state.settings = Settings(
        rag_default_top_k=3,
        rag_max_top_k=5,
        chat_history_limit=6,
        rate_limit_enabled=False,
    )
    app.state.job_store = FakeJobStore()
    app.state.history_store = history
    app.state.llm = FakeLlm()

    response = chat(ChatRequest(user_id="discord-user", message="Tìm job Data Engineer", top_k=3))

    assert response.answer.startswith("Có 1 job Data Engineer")
    assert response.sources[0].url == "https://example.com/job-1"
    assert history.added[0] == ("discord-user", "user", "Tìm job Data Engineer")
    assert history.added[1][1] == "assistant"
