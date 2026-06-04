from datetime import datetime, timezone

from api.config import Settings
from api.services.history_store import MongoChatHistoryStore


class FakeDeleteResult:
    deleted_count = 2


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def sort(self, *_args):
        return self

    def limit(self, limit):
        self.rows = self.rows[:limit]
        return self

    def __iter__(self):
        return iter(self.rows)


class FakeCollection:
    def __init__(self):
        self.inserted = []

    def insert_one(self, item):
        self.inserted.append(item)

    def find(self, *_args):
        return FakeCursor(
            [
                {"role": "assistant", "message": "Xin chào", "timestamp": datetime.now(timezone.utc)},
                {"role": "user", "message": "Tìm job data", "timestamp": datetime.now(timezone.utc)},
            ]
        )

    def delete_many(self, query):
        assert query == {"user_id": "123"}
        return FakeDeleteResult()


def test_history_store_read_write_delete_with_collection():
    collection = FakeCollection()
    store = MongoChatHistoryStore(Settings(), collection=collection)

    store.add_message("123", "user", "hello")
    history = store.recent_messages("123", 2)
    deleted = store.clear_user("123")

    assert collection.inserted[0]["user_id"] == "123"
    assert collection.inserted[0]["role"] == "user"
    assert history[0]["role"] == "user"
    assert deleted == 2
