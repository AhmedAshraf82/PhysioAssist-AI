
import uuid

from src.app.agents.prediagnosis_agent import PrediagnosisAgent
from src.app.models.chat_models import PrediagnoseAIResult
from src.app.utils.token_cost import calculate_run_cost_usd
import logging

logger = logging.getLogger(__name__)

async def process_prediagnose_message(
    chat_id: str | None,
    full_prompt: str,
) -> PrediagnoseAIResult:
    """
    Prediagnosis model execution for an already-built full prompt.
    """
    # Create a new unique chat id if none provided
    resolved_chat_id = chat_id or str(uuid.uuid4())

    # Create the prediagnosis agent
    prediagnosis_agent = PrediagnosisAgent.create_prediagnose_agent(
        name="PhysioAssist"
    )

    # Run the agent with the task
    task_result = await prediagnosis_agent.run(task=full_prompt)

    # Extract response
    ai_response = task_result.messages[-1].content
    user_tokens = task_result.messages[-1].models_usage.prompt_tokens
    assistant_tokens = task_result.messages[-1].models_usage.completion_tokens
    run_cost_usd = calculate_run_cost_usd(user_tokens, assistant_tokens)

    logger.info(
        "Prediagnose token usage (chat_id=%s, prompt_tokens=%s, completion_tokens=%s, run_cost_usd=%.8f)",
        resolved_chat_id,
        user_tokens,
        assistant_tokens,
        run_cost_usd,
    )
    
    return PrediagnoseAIResult(
        response=ai_response,
        llm_prompt_tokens=user_tokens,
        llm_completion_tokens=assistant_tokens,
        llm_cost_usd=run_cost_usd,
    )

