import os
from functools import lru_cache
from datetime import datetime

from openai import OpenAI

from src.app.core.config import settings
from src.app.services.db_handler.chat_session_handler import ChatSessionHandler
from src.app.services.db_handler.patient_handler import PatientHandler
from src.app.services.db_handler.schedule_handler import ScheduleHandler


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    """Create a singleton OpenAI client for deep-agent tools."""
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")
    return OpenAI(api_key=api_key)


def _resolve_user_id(*, user_id: str | None = None, chat_id: str | None = None) -> str | None:
    """Resolve canonical user ID from explicit input or linked chat session."""
    if user_id:
        return user_id

    if chat_id:
        with ChatSessionHandler() as chat_handler:
            session = chat_handler.get_session(chat_id)
        if session and session.get("user_id"):
            return str(session["user_id"])

    return None


def _phone_from_user_id(user_id: str | None) -> str | None:
    """Extract phone-like ID from WhatsApp user_id format (wa:<number>)."""
    if not user_id:
        return None
    if user_id.startswith("wa:"):
        return user_id.split(":", 1)[1]
    return None


def search_internet(query: str, max_results: int = 2) -> str:
    """Search internet for physiotherapy/injury information."""
    response = _get_openai_client().responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        tool_choice={"type": "web_search_preview"},
        input=f"Return up to {max_results} concise reliable findings for: {query}",
    )
    return response.output_text

def search_youtube(workout_query: str, max_results: int = 2) -> str:
    """Search YouTube videos for exercises/workouts using web search."""
    yt_query = f"site:youtube.com physiotherapy exercise video {workout_query}"
    response = _get_openai_client().responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        tool_choice={"type": "web_search_preview"},
        input=f"Find up to {max_results} useful YouTube videos for: {yt_query}. Return title + link.",
    )
    return response.output_text



def get_available_session_slots() -> str:
    """Return available clinic session slots from Mongo schedule collection."""
    with ScheduleHandler() as schedule_handler:
        slots = schedule_handler.get_available_slots(limit=15)

    if not slots:
        return "No available slots right now. Please try again shortly."

    lines = ["Available slots at V33 (El Waha, Cairo):"]
    for slot in slots:
        date_val = slot.get("date")
        if isinstance(date_val, datetime):
            lines.append(f"- {slot.get('day', '')}: {date_val.strftime('%Y-%m-%d %I:%M %p')}")
        else:
            lines.append(f"- {slot.get('day', '')}: {date_val}")

    return "\n".join(lines)


def add_schedule_slot(
    date: str,
    day: str,
    is_scheduled: bool = False,
    user_id: str | None = None,
    doctor: str = "",
) -> str:
    """Add/update one schedule slot.

    Args:
        date: Datetime string in ISO format, e.g. "2026-03-02T17:00:00"
        day: Weekday label, e.g. "Monday"
        is_scheduled: Whether slot is occupied
        user_id: Optional user id when occupied
        doctor: Optional doctor name/id (empty for now)
    """
    try:
        slot_dt = datetime.fromisoformat(date)
    except ValueError:
        return "Invalid date format. Use ISO format like 2026-03-02T17:00:00"

    with ScheduleHandler() as schedule_handler:
        slot = schedule_handler.add_slot(
            date=slot_dt,
            day=day,
            is_scheduled=is_scheduled,
            user_id=user_id,
            doctor=doctor,
        )

    return (
        "Slot saved: "
        f"date={slot['date']}, day={slot['day']}, is_scheduled={slot['is_scheduled']}, "
        f"user_id={slot['user_id']}, doctor={slot['doctor']}"
    )


def get_user_details(
    user_name: str | None = None,
    user_id: str | None = None,
    chat_id: str | None = None,
) -> str:
    """Get patient profile from MongoDB and ensure chat linkage.

    Linkage strategy:
    - Primary identity key: user_id
    - Session linkage: chat_id -> chat_sessions.user_id fallback
    - For WhatsApp, user_id already carries phone identity (e.g., wa:2010...)
    """
    resolved_user_id = _resolve_user_id(user_id=user_id, chat_id=chat_id)


    if not resolved_user_id:
        return "Please provide your user_id (or share a known chat/session) so I can retrieve your profile."

    with PatientHandler() as patient_handler:
        patient = patient_handler.get_by_user_id(resolved_user_id)

  
        if not patient:
            return "No stored patient profile found for this user yet."

        if chat_id:
            patient_handler.link_chat_session(resolved_user_id, chat_id)

    name = patient.get("full_name") or user_name or "Unknown"
    diagnosis = patient.get("diagnosis") or "Not set"
    medical_history = patient.get("medical_history") or "Not set"
    remaining = patient.get("remaining_sessions")
    total = patient.get("total_sessions")
    sessions_text = (
        f"{remaining} out of {total}" if remaining is not None and total is not None else "Not set"
    )

    return (
        f"User: {name}\n"
        f"User ID: {resolved_user_id}\n"
        f"Diagnosis: {diagnosis}\n"
        f"Medical history: {medical_history}\n"
        f"Remaining sessions: {sessions_text}"
    )


def schedule_appointment(
    user_name: str,
    preferred_day: str,
    preferred_time: str,
    user_id: str | None = None,
    chat_id: str | None = None,
) -> str:
    """Create appointment in `schedule` collection only (single responsibility)."""
    resolved_user_id = _resolve_user_id(user_id=user_id, chat_id=chat_id)
    if not resolved_user_id:
        return (
            "Cannot schedule yet because user identity is missing. "
            "Call get_user_details first (or provide user_id/chat_id)."
        )

    with ScheduleHandler() as schedule_handler:
        try:
            appointment = schedule_handler.create_appointment(
                user_id=resolved_user_id,
                chat_id=chat_id,
                patient_name=user_name,
                preferred_day=preferred_day,
                preferred_time=preferred_time,
                clinic_name="V33",
                clinic_location="El Waha, Cairo",
            )
        except ValueError as e:
            return f"Could not parse schedule request: {e}"

    if not appointment:
        return (
            f"Could not schedule {preferred_day} at {preferred_time}. "
            "Please ask for available slots and choose one of them."
        )

    date_value = appointment.get("date")
    date_text = (
        date_value.strftime("%Y-%m-%d %I:%M %p")
        if isinstance(date_value, datetime)
        else str(date_value)
    )

    return (
        f"Appointment confirmed for {user_name} at V33 (El Waha, Cairo) on {date_text}. "
        f"Linked to user {resolved_user_id}"
        + (f" and chat {chat_id}." if chat_id else ".")
    )
