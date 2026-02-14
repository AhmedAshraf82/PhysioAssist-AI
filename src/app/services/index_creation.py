"""
Index creation service for managing vector store indices.
Handles creation, configuration, and initialization of search indices.
"""

from typing import List, Optional
from src.app.vectorstores.search_factory import SearchServiceFactory
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class IndexCreationService:
    """Service for creating and managing vector store indices."""
    
    def __init__(self, search_service_type: str = settings.SEARCH_SERVICE_TYPE):
        """
        Initialize the index creation service.
        
        Args:
            search_service_type: Type of search service (elasticsearch or opensearch)
        """
        self.search_service_type = search_service_type
        
        # Create search service instance based on type
        if search_service_type == "elasticsearch":
            self.search_service = SearchServiceFactory.create_elasticsearch()
        elif search_service_type == "opensearch":
            self.search_service = SearchServiceFactory.create_opensearch()
        else:
            raise ValueError(f"Unsupported search service type: {search_service_type}")
        
        logger.info(f"IndexCreationService initialized with type: {search_service_type}")
    
    def create_index(
        self,
        index_name: str,
        vector_dimensions: int = settings.VECTOR_DIMENSIONS,
        text_fields: Optional[List[str]] = None,
        vector_field: str = "embedding"
    ) -> bool:
        """
        Create a new search index with vector capabilities.
        
        Args:
            index_name: Name of the index to create
            vector_dimensions: Dimension size for vector embeddings (default: 1536 for Titan)
            text_fields: List of text fields to include in the index
            vector_field: Name of the vector field (default: "embedding")
            
        Returns:
            bool: True if index created successfully
        """
        logger.info(f"Creating index: {index_name}")
        logger.debug(f"Vector dimensions: {vector_dimensions}")
        
        # Default text fields if not provided
        if text_fields is None:
            text_fields = ["title", "content", "category", "tags", "author"]
        
        try:
            # Create index with vector support using search service
            success = self.search_service.create_vector_index(
                index_name=index_name,
                text_fields=text_fields,
                vector_field=vector_field,
                vector_dims=vector_dimensions
            )
            
            if success:
                logger.info(f"✓ Index '{index_name}' created successfully")
            else:
                logger.warning(f"⚠ Index creation returned False for '{index_name}'")
            
            return success
        except Exception as e:
            logger.error(f"✗ Failed to create index '{index_name}': {e}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """
        Delete an existing index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            bool: True if index deleted successfully
        """
        logger.info(f"Deleting index: {index_name}")
        
        try:
            result = self.search_service.delete_index(index_name)
            logger.info(f"✓ Index '{index_name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete index '{index_name}': {e}")
            return False
    
    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name: Name of the index to check
            
        Returns:
            bool: True if index exists
        """
        try:
            exists = self.search_service.index_exists(index_name)
            logger.debug(f"Index '{index_name}' exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"✗ Error checking index existence: {e}")
            return False
    
    def get_document_count(self, index_name: str) -> int:
        """
        Get the number of documents in an index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            int: Number of documents in the index
        """
        try:
            count = self.search_service.get_document_count(index_name)
            logger.debug(f"Index '{index_name}' has {count} documents")
            return count
        except Exception as e:
            logger.error(f"✗ Error getting document count: {e}")
            return 0
