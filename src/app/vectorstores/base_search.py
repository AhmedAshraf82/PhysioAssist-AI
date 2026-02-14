from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseSearchService(ABC):
    """Abstract base class for search services"""
    
    @abstractmethod
    def create_index(self, index_name: str, mappings: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> bool:
        """Create an index with mappings and settings"""
        pass
    
    @abstractmethod
    def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        pass
    
    @abstractmethod
    def index_exists(self, index_name: str) -> bool:
        """Check if an index exists"""
        pass
    
    @abstractmethod
    def get_document_count(self, index_name: str) -> int:
        """Get the number of documents in an index"""
        pass
    
    @abstractmethod
    def clear_index(self, index_name: str) -> bool:
        """Delete all documents from an index without deleting the index itself"""
        pass
    
    @abstractmethod
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> bool:
        """Index a single document"""
        pass
    
    @abstractmethod
    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents"""
        pass
    
    @abstractmethod
    def full_text_search(self, index_name: str, query: str, fields: List[str], size: int = 10) -> List[Dict[str, Any]]:
        """Full-text search using BM25"""
        pass
    
    @abstractmethod
    def vector_search(self, index_name: str, vector: List[float], vector_field: str, size: int = 10) -> List[Dict[str, Any]]:
        """Vector similarity search"""
        pass
    
    @abstractmethod
    def hybrid_search(
        self, 
        index_name: str, 
        query: str, 
        vector: List[float], 
        text_fields: List[str],
        vector_field: str,
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining BM25 and vector similarity"""
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        pass
