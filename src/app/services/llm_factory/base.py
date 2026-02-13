"""Base provider abstract class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for LLM providers using ChatCompletionClient interface."""

    @abstractmethod
    def create(self, model: str, **kwargs: Any) -> Any:
        """
        Create a model client for the specific provider.
        
        Model clients should implement the ChatCompletionClient interface
        from autogen_agentchat.

        Args:
            model: The model name/identifier
            **kwargs: Additional provider-specific parameters (e.g., temperature, api_key)

        Returns:
            ChatCompletionClient: Model client instance
        """
        pass
