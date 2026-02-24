from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from src.app.services.db_handler.mongodb_handler import MongoDBHandler


class WhatsAppEventHandler(MongoDBHandler):
    """Stores processed WhatsApp webhook message IDs for idempotency."""

    def __init__(self):
        super().__init__(collection_name="whatsapp_processed_events")
        # Ensure idempotency key uniqueness and auto-cleanup for old records.
        self.collection.create_index("message_id", unique=True)
        self.collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)

    def register_inbound_if_new(self, message_id: str, chat_id: str | None = None) -> bool:
        """
        Returns True only when message_id is first seen.
        Returns False for duplicates.
        """
        if not message_id or not message_id.strip():
            return True

        try:
            result = self.collection.update_one(
                {"message_id": message_id},
                {
                    "$setOnInsert": {
                        "message_id": message_id,
                        "chat_id": chat_id,
                        "created_at": datetime.now(timezone.utc),
                    }
                },
                upsert=True,
            )
            return result.upserted_id is not None
        except PyMongoError:
            # Fail-open so webhook processing is not blocked by dedupe DB errors.
            return True
