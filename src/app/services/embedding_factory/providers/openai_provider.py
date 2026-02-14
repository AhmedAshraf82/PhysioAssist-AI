"""OpenAI embedding provider implementation."""

import os
from typing import Any, List, Optional
from openai import OpenAI
from ..base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider using the OpenAI SDK."""

    def __init__(self):
        self.client = None
        self.model = None

    def create(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> "OpenAIEmbeddingProvider":
        """
        Create an OpenAI embedding provider.

        Args:
            model: The OpenAI embedding model name (default: 'text-embedding-3-small')
                   Options: 'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'
            api_key: Optional API key (defaults to OPENAI_API_KEY env var)
            **kwargs: Additional parameters

        Returns:
            OpenAIEmbeddingProvider: Configured provider instance
            
        Example:
            >>> provider = OpenAIEmbeddingProvider()
            >>> provider.create("text-embedding-3-small")
            >>> embeddings = provider.embed("Hello, world!")
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        return self

    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If client is not initialized
        """
        if not self.client:
            raise ValueError("Client not initialized. Call create() first.")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating OpenAI embedding: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If client is not initialized
        """
        if not self.client:
            raise ValueError("Client not initialized. Call create() first.")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating OpenAI embeddings (batch): {e}")
            return []

    def get_dimensions(self) -> int:
        """
        Get the embedding dimensions for the current model.

        Returns:
            int: Number of dimensions
        """
        dimensions_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions_map.get(self.model, 1536)
