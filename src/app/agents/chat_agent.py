from autogen_agentchat.agents import AssistantAgent

from src.app.agents.prediagnosis_agent import PrediagnosisAgent


class ChatAgent:
    """Compatibility class exposing chat-oriented agent factory naming."""

    @staticmethod
    def create_chat_agent(
        name: str = "PhysioAssist",
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        system_message: str | None = None,
    ) -> AssistantAgent:
        kwargs: dict[str, object] = {
            "name": name,
            "provider": provider,
            "model": model,
            "temperature": temperature,
        }
        if system_message is not None:
            kwargs["system_message"] = system_message

        return PrediagnosisAgent.create_prediagnose_agent(**kwargs)
