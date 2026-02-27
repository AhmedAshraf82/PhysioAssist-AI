"""Patient collection handler for physiotherapy users."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from src.app.core.config import settings
from src.app.services.db_handler.mongodb_handler import MongoDBHandler
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class PatientHandler(MongoDBHandler):
    """Handler for the `patient` collection."""

    def __init__(self):
        super().__init__(
            collection_name="patient",
            connection_string=settings.MONGODB_CONNECTION_STRING,
            database_name=settings.MONGODB_DATABASE_NAME,
        )
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.collection.create_index("user_id", unique=True)
        self.collection.create_index("linked_chat_ids")
        self.collection.create_index("phone_number")

    def upsert_patient(
        self,
        *,
        user_id: str,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        diagnosis: Optional[str] = None,
        medical_history: Optional[str] = None,
        remaining_sessions: Optional[int] = None,
        total_sessions: Optional[int] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Create/update patient profile and optionally link a chat session."""
        now = datetime.utcnow()
        set_data: Dict[str, Any] = {"updated_at": now}

        if full_name is not None:
            set_data["full_name"] = full_name
        if phone_number is not None:
            set_data["phone_number"] = phone_number
        if diagnosis is not None:
            set_data["diagnosis"] = diagnosis
        if medical_history is not None:
            set_data["medical_history"] = medical_history
        if remaining_sessions is not None:
            set_data["remaining_sessions"] = int(remaining_sessions)
        if total_sessions is not None:
            set_data["total_sessions"] = int(total_sessions)

        update_doc: Dict[str, Any] = {
            "$set": set_data,
            "$setOnInsert": {
                "user_id": user_id,
                "created_at": now,
                "appointment_ids": [],
            },
        }

        # First: upsert base patient document.
        result = self.collection.update_one({"user_id": user_id}, update_doc, upsert=True)

        # Second: link chat in a separate update to avoid operator path conflicts.
        if chat_id:
            self.collection.update_one(
                {"user_id": user_id},
                {
                    "$addToSet": {"linked_chat_ids": chat_id},
                    "$set": {"updated_at": now},
                },
                upsert=True,
            )

        return bool(result.acknowledged)

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"user_id": user_id}, {"_id": 0})

    def get_by_chat_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"linked_chat_ids": chat_id}, {"_id": 0})

    def link_chat_session(self, user_id: str, chat_id: str) -> bool:
        result = self.collection.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"linked_chat_ids": chat_id},
                "$set": {"updated_at": datetime.utcnow()},
            },
            upsert=True,
        )
        return bool(result.acknowledged)

    def link_appointment(self, user_id: str, appointment_id: str) -> bool:
        result = self.collection.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"appointment_ids": appointment_id},
                "$set": {"updated_at": datetime.utcnow()},
            },
            upsert=True,
        )
        return bool(result.acknowledged)
