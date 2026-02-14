"""
RAG (Retrieval-Augmented Generation) service for searching indexed documents.
Supports full-text search (BM25), vector search, and hybrid search.
"""

from typing import List, Dict, Any, Optional
from src.app.vectorstores.search_factory import SearchServiceFactory


class RAGService:
    """Service for performing retrieval operations on vector stores."""
    
    def __init__(self, search_service_type: str = "elasticsearch"):
        """
        Initialize RAG service with specified search backend.
        
        Args:
            search_service_type: Type of search service ("elasticsearch" or "opensearch")
        """
        if search_service_type == "elasticsearch":
            self.search_service = SearchServiceFactory.create_elasticsearch()
        elif search_service_type == "opensearch":
            self.search_service = SearchServiceFactory.create_opensearch()
        else:
            raise ValueError(f"Unsupported search service type: {search_service_type}")
    
    def full_text_search(
        self,
        index_name: str,
        query: str,
        fields: List[str],
        size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search using BM25 algorithm.
        
        Args:
            index_name: Name of the index to search
            query: Search query text
            fields: List of fields to search in (e.g., ["title", "content"])
            size: Maximum number of results to return
            
        Returns:
            List of search results with scores and source documents
        """
        return self.search_service.full_text_search(
            index_name=index_name,
            query=query,
            fields=fields,
            size=size
        )
    
    def vector_search(
        self,
        index_name: str,
        query: str,
        vector_field: str = "embedding",
        size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            index_name: Name of the index to search
            query: Search query text (will be embedded)
            vector_field: Name of the vector field in index
            size: Maximum number of results to return
            
        Returns:
            List of search results with similarity scores and source documents
        """
        # Generate embedding for query
        query_vector = self.search_service.embed(query)
        
        return self.search_service.vector_search(
            index_name=index_name,
            vector=query_vector,
            vector_field=vector_field,
            size=size
        )
    
    def hybrid_search(
        self,
        index_name: str,
        query: str,
        text_fields: List[str],
        vector_field: str = "embedding",
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
        size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and vector similarity.
        
        Args:
            index_name: Name of the index to search
            query: Search query text
            text_fields: List of fields for full-text search
            vector_field: Name of the vector field in index
            text_weight: Weight for BM25 score (0.0 to 1.0)
            vector_weight: Weight for vector similarity score (0.0 to 1.0)
            size: Maximum number of results to return
            
        Returns:
            List of search results with combined scores and source documents
        """
        # Generate embedding for query
        query_vector = self.search_service.embed(query)
        
        return self.search_service.hybrid_search(
            index_name=index_name,
            query=query,
            vector=query_vector,
            text_fields=text_fields,
            vector_field=vector_field,
            text_weight=text_weight,
            vector_weight=vector_weight,
            size=size
        )
    
    def search(
        self,
        index_name: str,
        query: str,
        search_type: str = "hybrid",
        text_fields: Optional[List[str]] = None,
        vector_field: str = "embedding",
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
        size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Unified search method supporting multiple search types.
        
        Args:
            index_name: Name of the index to search
            query: Search query text
            search_type: Type of search ("full_text", "vector", or "hybrid")
            text_fields: List of fields for full-text search (required for full_text and hybrid)
            vector_field: Name of the vector field in index
            text_weight: Weight for BM25 score in hybrid search
            vector_weight: Weight for vector similarity in hybrid search
            size: Maximum number of results to return
            
        Returns:
            List of search results based on selected search type
        """
        if search_type == "full_text":
            if not text_fields:
                raise ValueError("text_fields required for full_text search")
            return self.full_text_search(index_name, query, text_fields, size)
        
        elif search_type == "vector":
            return self.vector_search(index_name, query, vector_field, size)
        
        elif search_type == "hybrid":
            if not text_fields:
                raise ValueError("text_fields required for hybrid search")
            return self.hybrid_search(
                index_name, query, text_fields, vector_field,
                text_weight, vector_weight, size
            )
        
        else:
            raise ValueError(f"Unsupported search type: {search_type}")
