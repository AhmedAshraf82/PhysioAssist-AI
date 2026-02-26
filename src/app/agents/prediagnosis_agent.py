from autogen_agentchat.agents import AssistantAgent
from src.app.core.config import settings
from src.app.services.llm_factory.llm_factory import LLMFactory
from src.app.tools.rag_tool import rag_search_tool

class PrediagnosisAgent:
    """Factory class for creating prediagnosis agents."""
    
    @staticmethod
    def create_prediagnose_agent(
        name: str = "PhysioAssist",
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
          system_message: str = """You are an Egyptian PhysioAssist, a world-class professional physiotherapist. Be concise, practical, and empathetic. If the user reports pain or injury, ask a few focused follow-up questions (location, onset, severity, triggers, relieving factors, and limitations), then provide likely causes, clear home-care recommendations, safe exercises if appropriate, and what activities to avoid. If there are red-flag symptoms or severe/worsening issues, advise urgent in-person medical evaluation. Always remind the user that your guidance is informational and not a definitive medical diagnosis. If the user's query is in English, respond in English. If it's in Arabic, respond in Egyptian Arabic. Use the language of the user's question for your response.""",
    ) -> AssistantAgent:
        """
        Create a prediagnosis agent with customizable parameters.
        
        Args:
            name: Agent name
            provider: LLM provider (e.g., "openai", "gemini")
            model: Model name
            temperature: Temperature for generation
            system_message: System message for the agent
            
        Returns:
            AssistantAgent configured for prediagnosis
        """
        model_client = LLMFactory.create(
            provider=settings.LLM_PROVIDER if provider is None else provider,
            model=settings.MODEL if model is None else model,
            temperature=settings.TEMPERATURE if temperature is None else temperature
        )
        
        agent = AssistantAgent(
            name=name,
            model_client=model_client,
            system_message=system_message,
            # tools=[rag_search_tool]  # Add any specific tools if needed
        )
        
        return agent
