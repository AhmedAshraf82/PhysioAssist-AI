"""LLM Factory with provider pattern for autogen and LangChain model clients."""

from typing import Any
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider
from .providers.grok_provider import GrokProvider
from .providers.llama_provider import LlamaProvider


class LLMFactory:
    """
    Factory class for creating model clients using different providers.
    
    Uses the new autogen model client pattern with ChatCompletionClient interface.
    
    Supports: OpenAI (implemented), Gemini (TODO), Grok (TODO), Llama (TODO).
    
    Example:
        >>> from autogen_agentchat.agents import AssistantAgent
        >>> 
        >>> # Create model client
        >>> model_client = LLMFactory.create("openai", "gpt-4o", temperature=0.7)
        >>> 
        >>> # Use with AssistantAgent
        >>> agent = AssistantAgent(
        ...     name="assistant",
        ...     model_client=model_client,
        ...     system_message="You are a helpful assistant."
        ... )
    """

    PROVIDERS = {
        "openai": OpenAIProvider(),
        "gemini": GeminiProvider(),
        "grok": GrokProvider(),
        "llama": LlamaProvider(),
    }

    @classmethod
    def create(cls, provider: str, model: str, **kwargs: Any) -> Any:
        """
        Create a model client for the specified provider and model.
        
        The returned model client implements the ChatCompletionClient interface
        and can be used with autogen_agentchat agents.

        Args:
            provider: The provider name ('openai', 'gemini', 'grok', 'llama')
            model: The model name/identifier
            **kwargs: Provider-specific parameters (e.g., temperature, api_key)

        Returns:
            ChatCompletionClient: Configured model client instance

        Raises:
            ValueError: If the provider is not supported
            NotImplementedError: If the provider is not yet implemented

        Examples:
            >>> # OpenAI (implemented)
            >>> model_client = LLMFactory.create("openai", "gpt-4o", temperature=0.7)
            >>> 
            >>> # With custom API key
            >>> model_client = LLMFactory.create(
            ...     "openai", 
            ...     "gpt-4", 
            ...     api_key="sk-...",
            ...     temperature=0.2
            ... )
            >>> 
            >>> # Other providers (TODO)
            >>> # model_client = LLMFactory.create("gemini", "gemini-pro")
            >>> # model_client = LLMFactory.create("grok", "grok-beta")
            >>> # model_client = LLMFactory.create("llama", "llama3")
        """
        provider = provider.lower()

        if provider not in cls.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(cls.PROVIDERS.keys())}"
            )

        return cls.PROVIDERS[provider].create(model, **kwargs)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        Get a list of all supported provider names.
        
        Note: Some providers may not be fully implemented yet.

        Returns:
            list[str]: List of supported provider names
        """
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def get_implemented_providers(cls) -> list[str]:
        """
        Get a list of fully implemented provider names.

        Returns:
            list[str]: List of implemented provider names
        """
        return ["openai"]  # TODO: Add others as they are implemented

    @classmethod
    def create_langchain_model(
        cls,
        provider: str,
        model: str,
        temperature: float = 0,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create a LangChain chat model for frameworks like deepagents.

        Supports provider indirection so app code can switch providers without
        rewriting agent creation logic.

        Args:
            provider: Provider name (e.g., ``openai``, ``ollama``, ``llama``).
            model: Model identifier for the provider.
            temperature: Sampling temperature.
            **kwargs: Provider-specific kwargs (e.g., ``api_key``, ``base_url``).

        Returns:
            BaseChatModel: LangChain-compatible chat model.
        """
        provider = provider.lower()

        if provider == "openai":
            return init_chat_model(
                model=model,
                model_provider="openai",
                temperature=temperature,
                **kwargs,
            )

        if provider in {"ollama", "llama"}:
            base_url = kwargs.pop("base_url", "http://localhost:11434")
            return init_chat_model(
                model=model,
                model_provider="ollama",
                temperature=temperature,
                base_url=base_url,
                **kwargs,
            )

        if provider == "gemini":
            return init_chat_model(
                model=model,
                model_provider="google_genai",
                temperature=temperature,
                **kwargs,
            )

        raise ValueError(
            f"Unsupported provider for LangChain model creation: {provider}. "
            "Supported: openai, ollama/llama, gemini"
        )
