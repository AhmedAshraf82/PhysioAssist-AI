"""Embedding Factory with provider pattern for different embedding services."""

from typing import Any
from .providers.openai_provider import OpenAIEmbeddingProvider
# from .providers.bedrock_provider import BedrockEmbeddingProvider


class EmbeddingFactory:
    """
    Factory class for creating embedding providers.
    
    Supports: OpenAI (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002),
              AWS Bedrock (amazon.titan-embed-text-v1)
    
    Example:
        >>> from embedding_factory import EmbeddingFactory
        >>> 
        >>> # Create OpenAI embedding provider (default)
        >>> embedder = EmbeddingFactory.create("openai", "text-embedding-3-small")
        >>> embeddings = embedder.embed("Hello, world!")
        >>> 
        >>> # Create Bedrock embedding provider
        >>> embedder = EmbeddingFactory.create("bedrock", "amazon.titan-embed-text-v1")
        >>> embeddings = embedder.embed("Hello, world!")
    """

    PROVIDERS = {
        "openai": OpenAIEmbeddingProvider,
        # "bedrock": BedrockEmbeddingProvider,
    }

    @classmethod
    def create(cls, provider: str, model: str = None, **kwargs: Any) -> Any:
        """
        Create an embedding provider for the specified provider and model.

        Args:
            provider: The provider name ('openai', 'bedrock')
            model: The model name/identifier (optional, uses provider defaults)
            **kwargs: Provider-specific parameters (e.g., api_key, aws_region)

        Returns:
            BaseEmbeddingProvider: Configured embedding provider instance

        Raises:
            ValueError: If the provider is not supported

        Examples:
            >>> # OpenAI with default model (text-embedding-3-small)
            >>> embedder = EmbeddingFactory.create("openai")
            >>> 
            >>> # OpenAI with specific model
            >>> embedder = EmbeddingFactory.create("openai", "text-embedding-3-large")
            >>> 
            >>> # With custom API key
            >>> embedder = EmbeddingFactory.create(
            ...     "openai", 
            ...     "text-embedding-3-small",
            ...     api_key="sk-..."
            ... )
            >>> 
            >>> # AWS Bedrock
            >>> embedder = EmbeddingFactory.create(
            ...     "bedrock",
            ...     "amazon.titan-embed-text-v1",
            ...     aws_region="us-east-1"
            ... )
        """
        provider = provider.lower()

        if provider not in cls.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(cls.PROVIDERS.keys())}"
            )

        provider_class = cls.PROVIDERS[provider]
        provider_instance = provider_class()
        
        if model:
            return provider_instance.create(model, **kwargs)
        else:
            return provider_instance.create(**kwargs)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        Get a list of all supported provider names.

        Returns:
            list[str]: List of supported provider names
        """
        return list(cls.PROVIDERS.keys())

    @classmethod
    def get_model_dimensions(cls, provider: str, model: str) -> int:
        """
        Get the embedding dimensions for a specific provider and model.

        Args:
            provider: The provider name
            model: The model name

        Returns:
            int: Number of dimensions

        Examples:
            >>> dims = EmbeddingFactory.get_model_dimensions("openai", "text-embedding-3-small")
            >>> print(dims)  # 1536
        """
        # Create a temporary instance to get dimensions
        embedder = cls.create(provider, model)
        return embedder.get_dimensions()
