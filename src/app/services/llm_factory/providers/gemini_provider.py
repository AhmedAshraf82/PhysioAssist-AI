"""Gemini provider implementation."""

import os
from typing import Any, Optional
from ..base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini model client provider."""

    def create(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any
    ) -> Any:
        """
        Create a Gemini model client.
        
        TODO: Implement using autogen_ext.models.gemini (or equivalent) once available.
        This should follow the pattern:
        
        from autogen_ext.models.gemini import GeminiChatCompletionClient
        
        return GeminiChatCompletionClient(
            model=model,
            api_key=api_key or os.getenv("GEMINI_API_KEY"),
            temperature=temperature,
            **kwargs
        )

        Args:
            model: The Gemini model name (e.g., 'gemini-pro', 'gemini-1.5-pro')
            api_key: Optional API key (defaults to GEMINI_API_KEY env var)
            temperature: The temperature setting (default: 0.2)
            **kwargs: Additional model client parameters

        Returns:
            ChatCompletionClient: Configured Gemini model client
        """
        raise NotImplementedError(
            "Gemini provider not yet implemented. "
            "Waiting for autogen_ext.models.gemini documentation."
        )
