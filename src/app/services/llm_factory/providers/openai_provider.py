"""OpenAI provider implementation."""

import os
from typing import Any, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from ..base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI model client provider using autogen_ext.models.openai."""

    def create(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any
    ) -> OpenAIChatCompletionClient:
        """
        Create an OpenAI model client.

        Args:
            model: The OpenAI model name (e.g., 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo')
            api_key: Optional API key (defaults to OPENAI_API_KEY env var)
            temperature: The temperature setting (default: 0.2)
            **kwargs: Additional OpenAIChatCompletionClient parameters

        Returns:
            OpenAIChatCompletionClient: Configured OpenAI model client
            
        Example:
            >>> provider = OpenAIProvider()
            >>> model_client = provider.create("gpt-4o", temperature=0.7)
        """
        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=temperature,
            **kwargs
        )
