"""AWS Bedrock embedding provider implementation."""

import os
import json
import boto3
from typing import Any, List, Optional
from ..base import BaseEmbeddingProvider


class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    """AWS Bedrock embedding provider using Amazon Titan."""

    def __init__(self):
        self.bedrock_runtime = None
        self.model = None

    def create(
        self,
        model: str = "amazon.titan-embed-text-v1",
        aws_region: Optional[str] = None,
        aws_profile: Optional[str] = None,
        **kwargs: Any
    ) -> "BedrockEmbeddingProvider":
        """
        Create an AWS Bedrock embedding provider.

        Args:
            model: The Bedrock model ID (default: 'amazon.titan-embed-text-v1')
            aws_region: AWS region (defaults to AWS_REGION env or 'us-east-1')
            aws_profile: AWS profile name (defaults to AWS_PROFILE env)
            **kwargs: Additional parameters

        Returns:
            BedrockEmbeddingProvider: Configured provider instance
        """
        aws_profile = aws_profile or os.getenv("AWS_PROFILE")
        aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")

        if aws_profile:
            session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
            self.bedrock_runtime = session.client("bedrock-runtime")
        else:
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime", 
                region_name=aws_region
            )

        self.model = model
        return self

    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text using AWS Bedrock.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If client is not initialized
        """
        if not self.bedrock_runtime:
            raise ValueError("Client not initialized. Call create() first.")

        try:
            body = json.dumps({"inputText": text})
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model,
                body=body,
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            return response_body.get("embedding", [])
        except Exception as e:
            print(f"Error generating Bedrock embedding: {e}")
            return []

    def get_dimensions(self) -> int:
        """
        Get the embedding dimensions for the current model.

        Returns:
            int: Number of dimensions
        """
        dimensions_map = {
            "amazon.titan-embed-text-v1": 1536,
            "amazon.titan-embed-text-v2": 1024,
        }
        return dimensions_map.get(self.model, 1536)
