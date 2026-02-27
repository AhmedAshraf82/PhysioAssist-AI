"""Schedule collection handler for physiotherapy appointments."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument

from src.app.core.config import settings
from src.app.services.db_handler.mongodb_handler import MongoDBHandler
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ScheduleHandler(MongoDBHandler):
    """Handler for the `schedule` collection."""

    def __init__(self):
        super().__init__(
            collection_name="schedule",
            connection_string=settings.MONGODB_CONNECTION_STRING,
            database_name=settings.MONGODB_DATABASE_NAME,
        )
        self._ensure_indexes()
        self._seed_default_slots_if_needed()

    def _ensure_indexes(self) -> None:
        # Requested schema indexes:
        # {date, day, is_scheduled, user_id, doctor}
        self.collection.create_index("date", unique=True)
        self.collection.create_index([("is_scheduled", 1), ("day", 1), ("date", 1)])
        self.collection.create_index([("user_id", 1), ("date", 1)])

    @staticmethod
    def _normalize_day(day: str) -> str:
        return day.strip().capitalize()

    @staticmethod
    def _parse_time(preferred_time: str) -> tuple[int, int]:
        t = preferred_time.strip().lower().replace(".", "")
        # Supports formats: "17:00", "5:00 pm", "5 pm"
        for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
            try:
                parsed = datetime.strptime(t, fmt)
                return parsed.hour, parsed.minute
            except ValueError:
                continue
        raise ValueError(f"Unsupported time format: {preferred_time}")

    def _next_datetime_for_day_time(self, preferred_day: str, preferred_time: str) -> datetime:
        day = self._normalize_day(preferred_day)
        target_weekday = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ].index(day)
        hour, minute = self._parse_time(preferred_time)

        now = datetime.utcnow()
        base = now.replace(second=0, microsecond=0)
        days_ahead = (target_weekday - base.weekday()) % 7
        candidate = base + timedelta(days=days_ahead)
        candidate = candidate.replace(hour=hour, minute=minute)
        if candidate < base:
            candidate = candidate + timedelta(days=7)
        return candidate

    def _seed_default_slots_if_needed(self, days_ahead: int = 21) -> None:
        """Seed upcoming slots if none exist in future."""
        now = datetime.utcnow()
        future_count = self.collection.count_documents({"date": {"$gte": now}})
        if future_count > 0:
            return

        template: dict[str, list[str]] = {
            "Sunday": ["10:00", "12:00", "17:00"],
            "Monday": ["11:00", "14:00", "18:00"],
            "Tuesday": ["09:30", "13:30", "16:30"],
            "Wednesday": ["10:30", "15:00"],
            "Thursday": ["12:30", "17:30"],
        }

        for offset in range(days_ahead + 1):
            d = (now + timedelta(days=offset)).replace(second=0, microsecond=0)
            day_name = d.strftime("%A")
            if day_name not in template:
                continue

            for hhmm in template[day_name]:
                hour, minute = [int(x) for x in hhmm.split(":", maxsplit=1)]
                slot_dt = d.replace(hour=hour, minute=minute)
                self.collection.update_one(
                    {"date": slot_dt},
                    {
                        "$setOnInsert": {
                            "date": slot_dt,
                            "day": day_name,
                            "is_scheduled": False,
                            "user_id": None,
                            "doctor": "",
                        }
                    },
                    upsert=True,
                )

    def add_slot(
        self,
        *,
        date: datetime,
        day: str,
        is_scheduled: bool = False,
        user_id: Optional[str] = None,
        doctor: str = "",
    ) -> Dict[str, Any]:
        """Create or upsert a schedule slot with requested schema fields.

        Schema:
        {
          "date": datetime,
          "day": str,
          "is_scheduled": bool,
          "user_id": str | None,
          "doctor": str
        }
        """
        normalized_day = self._normalize_day(day)
        doc = {
            "date": date,
            "day": normalized_day,
            "is_scheduled": bool(is_scheduled),
            "user_id": user_id if is_scheduled else None,
            "doctor": doctor or "",
        }
        self.collection.update_one({"date": date}, {"$set": doc}, upsert=True)
        return doc

    def create_appointment(
        self,
        *,
        user_id: str,
        chat_id: Optional[str],
        patient_name: str,
        preferred_day: str,
        preferred_time: str,
        clinic_name: str = "V33",
        clinic_location: str = "El Waha, Cairo",
        doctor: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Schedule on an existing available slot using requested schema."""
        slot_dt = self._next_datetime_for_day_time(preferred_day, preferred_time)
        day = self._normalize_day(preferred_day)

        result = self.collection.find_one_and_update(
            {
                "date": slot_dt,
                "day": day,
                "is_scheduled": False,
            },
            {
                "$set": {
                    "is_scheduled": True,
                    "user_id": user_id,
                    "doctor": doctor,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        # If slot doesn't exist yet, create and mark as scheduled.
        if not result:
            self.collection.update_one(
                {"date": slot_dt},
                {
                    "$setOnInsert": {
                        "date": slot_dt,
                        "day": day,
                    },
                    "$set": {
                        "is_scheduled": True,
                        "user_id": user_id,
                        "doctor": doctor,
                    },
                },
                upsert=True,
            )
            result = self.find_one({"date": slot_dt}, {"_id": 0})

        return result

    def get_available_slots(self, day: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "is_scheduled": False,
            "date": {"$gte": datetime.utcnow()},
        }
        if day:
            query["day"] = self._normalize_day(day)

        cursor = self.collection.find(query, {"_id": 0}).sort("date", 1).limit(limit)
        return list(cursor)

    def get_user_appointments(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.find_many(
            query={"user_id": user_id, "is_scheduled": True},
            projection={"_id": 0},
            limit=limit,
        )

    def get_by_datetime(self, date_value: datetime) -> Optional[Dict[str, Any]]:
        return self.find_one({"date": date_value}, {"_id": 0})
