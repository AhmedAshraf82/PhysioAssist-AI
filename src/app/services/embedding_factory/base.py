"""Base provider abstract class for embedding providers."""

from abc import ABC, abstractmethod
from typing import Any, List


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def create(self, model: str, **kwargs: Any) -> Any:
        """
        Create an embedding client for the specific provider.

        Args:
            model: The model name/identifier
            **kwargs: Additional provider-specific parameters (e.g., api_key)

        Returns:
            Embedding client instance
        """
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass
