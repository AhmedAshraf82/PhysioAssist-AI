from typing import Optional, List
from enum import Enum

from .base_search import BaseSearchService
from .elastic_search import ElasticSearchService
from .opensearch import OpenSearchService
from src.app.core.config import settings

class SearchServiceType(Enum):
    """Enum for available search service types"""
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"


class SearchServiceFactory:
    """Factory class for creating search service instances"""
    
    @staticmethod
    def create_search_service(
        service_type: SearchServiceType,
        hosts: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        cloud_id: Optional[str] = None,
        embedding_provider: str = settings.EMBEDDING_PROVIDER,
        embedding_model: str = settings.EMBEDDING_MODEL,
        **kwargs
    ) -> BaseSearchService:
        """
        Create a search service instance based on the specified type
        
        Args:
            service_type: Type of search service (ELASTICSEARCH or OPENSEARCH)
            hosts: List of host URLs
            username: Basic auth username
            password: Basic auth password
            api_key: API key for authentication
            cloud_id: Cloud ID (for Elastic Cloud)
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model name
            **kwargs: Additional service-specific parameters
            
        Returns:
            BaseSearchService: Instance of the requested search service
            
        Raises:
            ValueError: If invalid service type is provided
        """
        if service_type == SearchServiceType.ELASTICSEARCH:
            return ElasticSearchService(
                hosts=hosts,
                username=username,
                password=password,
                api_key=api_key,
                cloud_id=cloud_id,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model
            )
        elif service_type == SearchServiceType.OPENSEARCH:
            return OpenSearchService(
                hosts=hosts,
                username=username,
                password=password,
                api_key=api_key,
                cloud_id=cloud_id,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported search service type: {service_type}")
    
    @staticmethod
    def create_elasticsearch(
        hosts: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        cloud_id: Optional[str] = None,
        embedding_provider: str = settings.EMBEDDING_PROVIDER,
        embedding_model: str = settings.EMBEDDING_MODEL
    ) -> ElasticSearchService:
        """
        Convenience method to create an Elasticsearch service
        
        Args:
            hosts: List of Elasticsearch host URLs
            username: Basic auth username
            password: Basic auth password
            api_key: API key for authentication
            cloud_id: Elastic Cloud ID
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model name
            
        Returns:
            ElasticSearchService: Elasticsearch service instance
        """
        return ElasticSearchService(
            hosts=hosts,
            username=username,
            password=password,
            api_key=api_key,
            cloud_id=cloud_id,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model
        )
    
    @staticmethod
    def create_opensearch(
        hosts: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        cloud_id: Optional[str] = None,
        embedding_provider: str = settings.EMBEDDING_PROVIDER,
        embedding_model: str = settings.EMBEDDING_MODEL,
        **kwargs
    ) -> OpenSearchService:
        """
        Convenience method to create an OpenSearch service
        
        Args:
            hosts: List of OpenSearch host URLs
            username: Basic auth username
            password: Basic auth password
            api_key: API key for authentication
            cloud_id: Cloud ID (if applicable)
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model name
            **kwargs: Additional configuration parameters
            
        Returns:
            OpenSearchService: OpenSearch service instance
        """
        return OpenSearchService(
            hosts=hosts,
            username=username,
            password=password,
            api_key=api_key,
            cloud_id=cloud_id,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            **kwargs
        )
