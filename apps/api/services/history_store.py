from datetime import datetime, timezone

from api.config import Settings


class MongoChatHistoryStore:
    def __init__(self, settings: Settings, client=None, collection=None):
        self.client = client
        self.collection = collection
        if self.collection is not None:
            return

        from pymongo import MongoClient

        self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        self.collection = self.client[settings.mongodb_db][settings.mongodb_chat_collection]

    def healthcheck(self) -> None:
        if self.client is None:
            return
        self.client.admin.command("ping")

    def add_message(self, user_id: str, role: str, message: str) -> None:
        self.collection.insert_one(
            {
                "user_id": user_id,
                "role": role,
                "message": message,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    def recent_messages(self, user_id: str, limit: int) -> list[dict[str, str]]:
        cursor = (
            self.collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "message": 1, "timestamp": 1})
            .sort("timestamp", -1)
            .limit(limit)
        )
        messages = list(cursor)
        messages.reverse()
        return [{"role": str(item["role"]), "message": str(item["message"])} for item in messages]

    def clear_user(self, user_id: str) -> int:
        result = self.collection.delete_many({"user_id": user_id})
        return int(result.deleted_count)
