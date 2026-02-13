from autogen_agentchat.agents import AssistantAgent
from src.app.services.llm_factory.llm_factory import LLMFactory


class PrediagnosisAgent:
    """Factory class for creating prediagnosis agents."""
    
    @staticmethod
    def create_prediagnose_agent(
        name: str = "PhysioAssist",
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        temperature: float = 0,
        system_message: str = "You are a helpful physiotherapy assistant. Provide clear, accurate information about physiotherapy, exercises, and wellness."
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
            provider=provider,
            model=model,
            temperature=temperature
        )
        
        agent = AssistantAgent(
            name=name,
            model_client=model_client,
            system_message=system_message,
        )
        
        return agent
