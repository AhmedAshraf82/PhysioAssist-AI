import logging
import uuid
from typing import Awaitable, Callable

from src.app.agents.chat_agent import ChatAgent
from src.app.models.channel_models import UnifiedInboundMessage, UnifiedOutboundMessage
from src.app.models.chat_models import ChatAIResult
from src.app.services.channels.orchestrator import process_unified_message
from src.app.services.db_handler.chat_session_handler import ChatSessionHandler
from src.app.utils.token_cost import (
    calculate_run_cost_usd,
    calculate_total_interaction_cost_usd,
)

logger = logging.getLogger(__name__)

AiProcessor = Callable[[str | None, str, str | None], Awaitable[object]]


def _build_usage_metadata(
    llm_prompt_tokens: int,
    llm_completion_tokens: int,
    stt_text_input_tokens: int,
    stt_text_output_tokens: int,
    stt_audio_input_tokens: int,
    tts_text_input_tokens: int,
    tts_audio_output_tokens: int,
    total_run_cost_usd: float,
) -> dict[str, dict]:
    return {
        "usage": {
            "llm": {
                "prompt_tokens": int(llm_prompt_tokens),
                "completion_tokens": int(llm_completion_tokens),
            },
            "stt": {
                "text_input_tokens": int(stt_text_input_tokens),
                "text_output_tokens": int(stt_text_output_tokens),
                "audio_input_tokens": int(stt_audio_input_tokens),
            },
            "tts": {
                "text_input_tokens": int(tts_text_input_tokens),
                "audio_output_tokens": int(tts_audio_output_tokens),
            },
        },
        "costs": {
            "total_run_cost_usd": float(total_run_cost_usd),
        },
    }


def build_usage_metadata_from_outbound(
    outbound: UnifiedOutboundMessage,
) -> dict[str, dict]:
    llm_usage = outbound.metadata.get("llm_usage", {}) if outbound.metadata else {}
    stt_usage = outbound.metadata.get("stt_usage", {}) if outbound.metadata else {}
    tts_usage = outbound.metadata.get("tts_usage", {}) if outbound.metadata else {}

    llm_prompt_tokens = int(llm_usage.get("prompt_tokens", 0) or 0)
    llm_completion_tokens = int(llm_usage.get("completion_tokens", 0) or 0)
    stt_text_input_tokens = int(stt_usage.get("text_input_tokens", 0) or 0)
    stt_text_output_tokens = int(stt_usage.get("text_output_tokens", 0) or 0)
    stt_audio_input_tokens = int(stt_usage.get("audio_input_tokens", 0) or 0)
    tts_text_input_tokens = int(tts_usage.get("text_input_tokens", 0) or 0)
    tts_audio_output_tokens = int(tts_usage.get("audio_output_tokens", 0) or 0)

    total_run_cost_usd = calculate_total_interaction_cost_usd(
        llm_prompt_tokens=llm_prompt_tokens,
        llm_completion_tokens=llm_completion_tokens,
        stt_text_input_tokens=stt_text_input_tokens,
        stt_text_output_tokens=stt_text_output_tokens,
        stt_audio_input_tokens=stt_audio_input_tokens,
        tts_text_input_tokens=tts_text_input_tokens,
        tts_audio_output_tokens=tts_audio_output_tokens,
    )

    return _build_usage_metadata(
        llm_prompt_tokens=llm_prompt_tokens,
        llm_completion_tokens=llm_completion_tokens,
        stt_text_input_tokens=stt_text_input_tokens,
        stt_text_output_tokens=stt_text_output_tokens,
        stt_audio_input_tokens=stt_audio_input_tokens,
        tts_text_input_tokens=tts_text_input_tokens,
        tts_audio_output_tokens=tts_audio_output_tokens,
        total_run_cost_usd=total_run_cost_usd,
    )


def persist_unified_chat_turn(
    unified: UnifiedInboundMessage,
    outbound: UnifiedOutboundMessage,
    fallback_user_text: str,
    user_mime_type: str,
) -> int:
    metadata = build_usage_metadata_from_outbound(outbound)

    with ChatSessionHandler() as handler:
        normalized_user_text = (
            outbound.metadata.get("normalized_user_text") if outbound.metadata else None
        ) or fallback_user_text

        handler.add_message(
            unified.chat_id,
            normalized_user_text,
            "user",
            mime_type=user_mime_type,
            user_id=unified.user_id,
            metadata=metadata,
        )

        handler.add_message(
            unified.chat_id,
            outbound.text,
            "assistant",
            mime_type="TEXT",
            user_id=unified.user_id,
            metadata=metadata,
        )

        return handler.get_message_count(unified.chat_id)


def persist_text_chat_turn(
    chat_id: str,
    user_id: str,
    user_text: str,
    assistant_text: str,
    ai_result: ChatAIResult,
    user_mime_type: str = "TEXT",
) -> int:
    metadata = _build_usage_metadata(
        llm_prompt_tokens=int(ai_result.llm_prompt_tokens),
        llm_completion_tokens=int(ai_result.llm_completion_tokens),
        stt_text_input_tokens=0,
        stt_text_output_tokens=0,
        stt_audio_input_tokens=0,
        tts_text_input_tokens=0,
        tts_audio_output_tokens=0,
        total_run_cost_usd=float(ai_result.llm_cost_usd),
    )

    with ChatSessionHandler() as handler:
        handler.add_message(
            chat_id,
            user_text,
            "user",
            mime_type=user_mime_type,
            user_id=user_id,
            metadata=metadata,
        )
        handler.add_message(
            chat_id,
            assistant_text,
            "assistant",
            mime_type="TEXT",
            user_id=user_id,
            metadata=metadata,
        )

        return handler.get_message_count(chat_id)


def build_chat_ai_processor(default_chat_id: str) -> AiProcessor:
    """Create an ai_processor compatible callable for unified message orchestration."""

    async def _ai_processor(
        chat_id: str | None,
        message: str,
        user_id: str | None = None,
    ) -> ChatAIResult:
        resolved_chat_id = chat_id or default_chat_id
        with ChatSessionHandler() as handler:
            full_prompt = handler.build_context_prompt(resolved_chat_id, message)
        return await process_chat_message(resolved_chat_id, full_prompt)

    return _ai_processor


async def process_unified_chat_message(
    incoming: UnifiedInboundMessage,
) -> UnifiedOutboundMessage:
    """Run the shared unified-message pipeline using chat ai processor defaults."""
    return await process_unified_message(
        incoming=incoming,
        ai_processor=build_chat_ai_processor(incoming.chat_id),
    )


async def process_chat_message(
    chat_id: str | None,
    full_prompt: str,
) -> ChatAIResult:
    """Chat model execution for an already-built full prompt."""
    resolved_chat_id = chat_id or str(uuid.uuid4())

    chat_agent = ChatAgent.create_chat_agent(name="PhysioAssist")
    task_result = await chat_agent.run(task=full_prompt)

    ai_response = task_result.messages[-1].content
    user_tokens = task_result.messages[-1].models_usage.prompt_tokens
    assistant_tokens = task_result.messages[-1].models_usage.completion_tokens
    run_cost_usd = calculate_run_cost_usd(user_tokens, assistant_tokens)

    logger.info(
        "Chat token usage (chat_id=%s, prompt_tokens=%s, completion_tokens=%s, run_cost_usd=%.8f)",
        resolved_chat_id,
        user_tokens,
        assistant_tokens,
        run_cost_usd,
    )

    return ChatAIResult(
        response=ai_response,
        llm_prompt_tokens=user_tokens,
        llm_completion_tokens=assistant_tokens,
        llm_cost_usd=run_cost_usd,
    )
