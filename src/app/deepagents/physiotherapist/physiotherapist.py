import os
import logging

from deepagents import create_deep_agent

from src.app.core.config import settings
from src.app.deepagents.physiotherapist.tools import (
    add_schedule_slot,
    get_available_session_slots,
    search_internet,
    search_youtube,
    get_user_details,
    schedule_appointment,
)
from src.app.services.llm_factory.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


def _configure_langsmith() -> None:
    """Configure LangSmith tracing from app settings/env.
    """
    tracing_enabled = str(settings.LANGSMITH_TRACING).lower() == "true"
    if not tracing_enabled:
        return

    langsmith_api_key = settings.LANGSMITH_API_KEY or os.getenv("LANGSMITH_API_KEY")
    if not langsmith_api_key:
        # Do not block chat flow in production if tracing key is absent.
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.warning(
            "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing. "
            "Continuing with tracing disabled."
        )
        return

    os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT or "physio"

    if settings.LANGSMITH_ENDPOINT:
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    if settings.LANGSMITH_WORKSPACE_ID:
        os.environ["LANGSMITH_WORKSPACE_ID"] = settings.LANGSMITH_WORKSPACE_ID


class PhysiotherapistAgent:
    """Factory class for creating the physiotherapist deep agent."""
    
    @staticmethod
    def create_agent():
        """Create and return the configured physiotherapist deep agent."""
        _configure_langsmith()

        provider = settings.LLM_PROVIDER
        model_name = settings.MODEL
        temperature = settings.TEMPERATURE

        model = LLMFactory.create_langchain_model(
            provider=provider,
            model=model_name,
            temperature=temperature,
        )

        system_prompt = """You are a general physiotherapy assistant for V33 clinic in El Waha, Cairo.
        You help users with pain/injury/physiotherapy questions and clinic operations.

        Clinic context:
        - Name: V33
        - Location: El Waha, Cairo
        - Focus: physiotherapy, rehabilitation, and injury recovery

        Tool usage policy:
        1) If user asks about sessions/availability -> use get_available_session_slots.
        2) If user asks clinical education or injury/pain info -> use search_internet.
        3) If user asks for exercise/workout videos -> use search_youtube.
        4) If user asks about profile/history/sessions -> use get_user_details.
          5) If user asks to book/confirm appointment:
              - First call get_user_details using user_id/chat_id from SESSION_METADATA.
              - Then call schedule_appointment with the resolved identity.
        6) If admin/staff asks to add or update a slot -> use add_schedule_slot.

        Identity and linking rules:
        - A [SESSION_METADATA] block may be present in user context with chat_id and user_id.
        - Always pass user_id and chat_id to get_user_details/schedule_appointment when available.
        - This ensures patient records are linked to appointments and chat sessions.

        Safety policy:
        - Give educational guidance only; do not provide definitive diagnosis.
        - Escalate urgent red flags to immediate in-person care.
        """

        agent = create_deep_agent(
            model=model,
            system_prompt=system_prompt,
            tools=[
                add_schedule_slot,
                get_available_session_slots,
                search_internet,
                search_youtube,
                get_user_details,
                schedule_appointment,
            ],
        )
        return agent


class PrediagnosisAgent:
    """Backward-compatible wrapper for older imports."""

    @staticmethod
    def create_prediagnose_agent():
        return PhysiotherapistAgent.create_agent()
