"""
Indexer service for processing and storing document chunks in vector stores.
Handles embedding generation and batch indexing operations.
"""

from typing import List, Dict, Any
from src.app.vectorstores.search_factory import SearchServiceFactory
from src.app.utils.logger import setup_logger
from src.app.core.config import settings
logger = setup_logger(__name__)


class IndexerService:
    """Service for indexing document chunks into vector stores."""
    
    def __init__(
        self,
        search_service_type: str = settings.SEARCH_SERVICE_TYPE,
        embedding_provider: str = settings.EMBEDDING_PROVIDER,
        embedding_model: str = settings.EMBEDDING_MODEL
    ):
        """
        Initialize the indexer service.
        
        Args:
            search_service_type: Type of search service (elasticsearch or opensearch)
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model to use
        """
        self.search_service_type = search_service_type
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        
        # Create search service instance based on type
        if search_service_type == "elasticsearch":
            self.search_service = SearchServiceFactory.create_elasticsearch(
                embedding_provider=embedding_provider,
                embedding_model=embedding_model
            )
        elif search_service_type == "opensearch":
            self.search_service = SearchServiceFactory.create_opensearch(
                embedding_provider=embedding_provider,
                embedding_model=embedding_model
            )
        else:
            raise ValueError(f"Unsupported search service type: {search_service_type}")
        
        logger.info(f"IndexerService initialized with {search_service_type}")
        logger.debug(f"Using embedding provider: {embedding_provider}, model: {embedding_model}")
    
    def index_chunks(
        self,
        index_name: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Index document chunks with embeddings into the vector store.
        
        Args:
            index_name: Name of the target index
            chunks: List of document chunks with metadata
                Each chunk should have: {
                    "content": str,
                    "title": str (optional),
                    "category": str (optional),
                    "tags": List[str] (optional),
                    "author": str (optional),
                    "url": str (optional),
                    "source": str (optional)
                }
            
        Returns:
            dict: Indexing statistics {
                "total_chunks": int,
                "indexed_count": int,
                "failed_count": int,
                "errors": List[str]
            }
        """
        logger.info(f"Starting indexing process for index: {index_name}")
        logger.info(f"Total chunks to index: {len(chunks)}")
        
        stats = {
            "total_chunks": len(chunks),
            "indexed_count": 0,
            "failed_count": 0,
            "errors": []
        }
        
        try:
            # Process chunks and generate embeddings
            documents_with_embeddings = []
            
            for i, chunk in enumerate(chunks, 1):
                logger.debug(f"Processing chunk {i}/{len(chunks)}")
                
                try:
                    # Generate embedding for the content
                    content = chunk.get("content", "")
                    embedding = self.search_service.embed(content)
                    
                    # Create document with embedding
                    doc_with_embedding = chunk.copy()
                    doc_with_embedding['embedding'] = embedding
                    documents_with_embeddings.append(doc_with_embedding)
                    
                except Exception as e:
                    logger.error(f"Failed to process chunk {i}: {e}")
                    stats["failed_count"] += 1
                    stats["errors"].append(f"Chunk {i}: {str(e)}")
            
            # Bulk index all documents with embeddings
            if documents_with_embeddings:
                logger.info(f"Bulk indexing {len(documents_with_embeddings)} documents...")
                success = self.search_service.bulk_index(index_name, documents_with_embeddings)
                
                if success:
                    stats["indexed_count"] = len(documents_with_embeddings)
                    logger.info(f"✓ Bulk indexing completed successfully")
                else:
                    stats["failed_count"] = len(documents_with_embeddings)
                    logger.error(f"✗ Bulk indexing failed")
            
            logger.info(f"✓ Indexing completed")
            logger.info(f"  - Total chunks: {stats['total_chunks']}")
            logger.info(f"  - Indexed: {stats['indexed_count']}")
            logger.info(f"  - Failed: {stats['failed_count']}")
            
            return stats
        
        except Exception as e:
            logger.error(f"✗ Indexing failed: {e}")
            stats["errors"].append(str(e))
            return stats
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using configured embedding provider.
        
        Args:
            text: Text string to embed
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            embedding = self.search_service.embed(text)
            logger.debug(f"✓ Generated embedding for text ({len(text)} chars)")
            return embedding
        except Exception as e:
            logger.error(f"✗ Embedding generation failed: {e}")
            raise
    
    def delete_by_query(
        self,
        index_name: str,
        query: Dict[str, Any]
    ) -> int:
        """
        Delete documents from index based on a query.
        
        Args:
            index_name: Name of the target index
            query: Elasticsearch/OpenSearch query to match documents
            
        Returns:
            int: Number of documents deleted
        """
        logger.info(f"Deleting documents from index: {index_name}")
        logger.debug(f"Query: {query}")
        
        try:
            # Note: This would need to be implemented in the search service
            # deleted_count = self.search_service.delete_by_query(
            #     index_name=index_name,
            #     query=query
            # )
            # logger.info(f"✓ Deleted {deleted_count} documents")
            # return deleted_count
            logger.warning("delete_by_query not yet implemented in search service")
            return 0
        except Exception as e:
            logger.error(f"✗ Deletion failed: {e}")
            return 0
