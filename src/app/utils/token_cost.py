from src.app.core.config import settings


# Pricing in USD per 1M tokens (official list provided by user)
_PRICING_PER_1M = {
    "gpt-4o": {
        "input": 2.50,
        "cached_input": 1.25,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "cached_input": 0.075,
        "output": 0.60,
    },
}


def _normalize_model(model_name: str) -> str:
    """Normalize model aliases/versions to supported pricing keys."""
    normalized = (model_name or "").strip().lower()

    # Handle versioned names like gpt-4o-2024-08-06
    if normalized.startswith("gpt-4o-mini"):
        return "gpt-4o-mini"
    if normalized.startswith("gpt-4o"):
        return "gpt-4o"

    return normalized


def calculate_run_cost_usd(user_tokens: int, assistant_tokens: int) -> float:
    """
    Calculate total USD cost for one model run from prompt/output token counts.

    Uses configured model from settings.MODEL.

    Args:
        user_tokens: Prompt/input tokens.
        assistant_tokens: Completion/output tokens.

    Returns:
        Total run cost in USD as float.

    Raises:
        ValueError: If configured model is unsupported by pricing table.
    """
    model_key = _normalize_model(settings.MODEL)
    pricing = _PRICING_PER_1M.get(model_key)

    if pricing is None:
        raise ValueError(
            f"Unsupported model for cost calculation: {settings.MODEL}. "
            f"Supported: {', '.join(_PRICING_PER_1M.keys())}"
        )

    input_cost = (max(user_tokens, 0) / 1_000_000) * pricing["input"]
    output_cost = (max(assistant_tokens, 0) / 1_000_000) * pricing["output"]

    return float(input_cost + output_cost)


def calculate_total_interaction_cost_usd(
    llm_prompt_tokens: int,
    llm_completion_tokens: int,
    stt_text_input_tokens: int = 0,
    stt_text_output_tokens: int = 0,
    stt_audio_input_tokens: int = 0,
    tts_text_input_tokens: int = 0,
    tts_audio_output_tokens: int = 0,
) -> float:
    """Calculate total USD cost for one interaction (LLM + STT + TTS)."""
    llm_cost = calculate_run_cost_usd(llm_prompt_tokens, llm_completion_tokens)

    # STT (gpt-4o-transcribe) pricing per 1M tokens
    stt_cost = (
        (max(stt_text_input_tokens, 0) / 1_000_000) * 2.50
        + (max(stt_text_output_tokens, 0) / 1_000_000) * 10.00
        + (max(stt_audio_input_tokens, 0) / 1_000_000) * 6.00
    )

    # TTS (gpt-4o-mini-tts) pricing per 1M tokens
    tts_cost = (
        (max(tts_text_input_tokens, 0) / 1_000_000) * 0.60
        + (max(tts_audio_output_tokens, 0) / 1_000_000) * 12.00
    )

    return float(llm_cost + stt_cost + tts_cost)





def extract_text_and_usage(agent_result: dict) -> tuple[str, int, int]:
    """Extract assistant text and token usage from deepagents invoke result."""
    messages = agent_result.get("messages", [])
    if not messages:
        return "", 0, 0

    last = messages[-1]
    content = getattr(last, "content", "")

    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        text = "\n".join(p for p in parts if p).strip()
    else:
        text = str(content)

    usage = getattr(last, "usage_metadata", {}) or {}
    prompt_tokens = int(
        usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or usage.get("input_token_count")
        or 0
    )
    completion_tokens = int(
        usage.get("output_tokens")
        or usage.get("completion_tokens")
        or usage.get("output_token_count")
        or 0
    )

    return text, prompt_tokens, completion_tokens
