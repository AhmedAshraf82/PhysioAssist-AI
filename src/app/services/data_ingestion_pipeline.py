"""
Data ingestion pipeline for indexing documents into vector stores.
Orchestrates the complete flow: index creation -> data fetching -> embedding -> indexing.
"""

from typing import Dict, Any, Optional, List
from src.app.services.index_creation import IndexCreationService
from src.app.services.indexer import IndexerService
from src.app.vectorstores.sample_data import get_sample_documents
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataIngestionPipeline:
    """Pipeline for ingesting data into vector stores."""
    
    def __init__(
        self,
        search_service_type: str = settings.SEARCH_SERVICE_TYPE,
        embedding_provider: str = settings.EMBEDDING_PROVIDER,
        embedding_model: str = settings.EMBEDDING_MODEL
    ):
        """
        Initialize the data ingestion pipeline.
        
        Args:
            search_service_type: Type of search service (elasticsearch or opensearch)
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model to use
        """
        self.search_service_type = search_service_type
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        
        logger.info(f"DataIngestionPipeline initialized")
        logger.debug(f"Search service: {search_service_type}")
        logger.debug(f"Embedding: {embedding_provider}/{embedding_model}")
    
    def run(
        self,
        index_name: Optional[str] = None,
        vector_dimensions: int = settings.VECTOR_DIMENSIONS,
        text_fields: Optional[List[str]] = None,
        recreate_index: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete data ingestion pipeline.
        
        Args:
            index_name: Name of the index (defaults to settings.INDEX_NAME)
            vector_dimensions: Dimension size for vector embeddings
            text_fields: List of text fields to include in the index
            recreate_index: If True, delete and recreate the index if it exists
            
        Returns:
            dict: Pipeline execution results with statistics
        """
        # Use default index name if not provided
        if index_name is None:
            index_name = settings.INDEX_NAME
        
        # Default text fields if not provided
        if text_fields is None:
            text_fields = ["title", "content", "tags", "body_part", "injury_name"]
        
        logger.info("="*80)
        logger.info("Starting Data Ingestion Pipeline")
        logger.info("="*80)
        logger.info(f"Target index: {index_name}")
        logger.info(f"Vector dimensions: {vector_dimensions}")
        logger.info(f"Text fields: {text_fields}")
        
        results = {
            "success": False,
            "index_name": index_name,
            "index_created": False,
            "index_existed": False,
            "initial_document_count": 0,
            "documents_deleted": 0,
            "documents_fetched": 0,
            "documents_indexed": 0,
            "documents_failed": 0,
            "final_document_count": 0,
            "errors": [],
            "message": ""
        }
        
        try:
            # Step 1: Create or verify index
            logger.info("\n--- STEP 1: Index Creation ---")
            index_service = IndexCreationService(search_service_type=self.search_service_type)
            
            # Check if index exists
            if index_service.index_exists(index_name):
                results["index_existed"] = True
                # Get initial document count
                results["initial_document_count"] = index_service.get_document_count(index_name)
                logger.info(f"Index '{index_name}' exists with {results['initial_document_count']} documents")
                
                if recreate_index:
                    logger.info(f"Recreating index (will delete {results['initial_document_count']} documents)...")
                    results["documents_deleted"] = results["initial_document_count"]
                    index_service.delete_index(index_name)
                    create_success = index_service.create_index(
                        index_name=index_name,
                        vector_dimensions=vector_dimensions,
                        text_fields=text_fields
                    )
                    if not create_success:
                        results["errors"].append("Failed to recreate index")
                        results["message"] = "Index recreation failed"
                        logger.error("✗ Failed to recreate index")
                        return results
                    results["index_created"] = True
                    logger.info(f"✓ Index '{index_name}' recreated successfully")
                else:
                    logger.info(f"✓ Index '{index_name}' already exists, using existing")
            else:
                logger.info(f"Creating new index: {index_name}")
                create_success = index_service.create_index(
                    index_name=index_name,
                    vector_dimensions=vector_dimensions,
                    text_fields=text_fields
                )
                if not create_success:
                    results["errors"].append("Failed to create index")
                    results["message"] = "Index creation failed"
                    logger.error("✗ Failed to create index")
                    return results
                results["index_created"] = True
                logger.info(f"✓ Index '{index_name}' created successfully")
            
            # Step 2: Fetch documents
            logger.info("\n--- STEP 2: Data Fetching ---")
            # TODO: Replace with MongoDB data fetching
            # from src.app.services.db_handler.mongodb import get_documents_from_mongodb
            # documents = get_documents_from_mongodb()
            documents = get_sample_documents()
            results["documents_fetched"] = len(documents)
            logger.info(f"✓ Fetched {len(documents)} documents from data source")
            logger.warning("⚠️  TODO: Replace get_sample_documents() with MongoDB fetching")
            
            if not documents:
                results["errors"].append("No documents to index")
                results["message"] = "No documents fetched from data source"
                logger.warning("⚠️  No documents to index")
                return results
            
            # Step 3: Index documents with embeddings
            logger.info("\n--- STEP 3: Document Indexing ---")
            indexer = IndexerService(
                search_service_type=self.search_service_type,
                embedding_provider=self.embedding_provider,
                embedding_model=self.embedding_model
            )
            
            indexing_stats = indexer.index_chunks(
                index_name=index_name,
                chunks=documents
            )
            
            results["documents_indexed"] = indexing_stats["indexed_count"]
            results["documents_failed"] = indexing_stats["failed_count"]
            results["errors"].extend(indexing_stats["errors"])
            
            # Step 4: Verify indexing
            logger.info("\n--- STEP 4: Verification ---")
            results["final_document_count"] = index_service.get_document_count(index_name)
            logger.info(f"✓ Final document count in index: {results['final_document_count']}")
            
            # Create detailed message
            message_parts = []
            if results["index_existed"]:
                message_parts.append(f"Index contained {results['initial_document_count']} docs")
            if results["documents_deleted"] > 0:
                message_parts.append(f"{results['documents_deleted']} deleted")
            message_parts.append(f"{results['documents_fetched']} fetched")
            message_parts.append(f"{results['documents_indexed']} indexed")
            if results["documents_failed"] > 0:
                message_parts.append(f"{results['documents_failed']} failed")
            message_parts.append(f"Current index count: {results['final_document_count']}")
            
            detailed_message = ", ".join(message_parts)
            
            # Determine success
            if results["documents_indexed"] == results["documents_fetched"]:
                results["success"] = True
                results["message"] = f"Successfully ingested all documents. {detailed_message}"
                logger.info("✓ Data ingestion completed successfully!")
            elif results["documents_indexed"] > 0:
                results["success"] = True
                results["message"] = f"Partially successful. {detailed_message}"
                logger.warning(f"⚠️  Partial success: {results['documents_indexed']}/{results['documents_fetched']} documents indexed")
            else:
                results["message"] = f"Failed to index any documents. {detailed_message}"
                logger.error("✗ Failed to index any documents")
            
            logger.info("="*80)
            logger.info("Data Ingestion Pipeline Completed")
            logger.info("="*80)
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Pipeline failed with error: {e}")
            results["errors"].append(str(e))
            results["message"] = f"Pipeline error: {str(e)}"
            return results
    
    def get_index_info(self, index_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an index.
        
        Args:
            index_name: Name of the index (defaults to settings.INDEX_NAME)
            
        Returns:
            dict: Index information
        """
        if index_name is None:
            index_name = settings.INDEX_NAME
        
        try:
            index_service = IndexCreationService(search_service_type=self.search_service_type)
            
            exists = index_service.index_exists(index_name)
            doc_count = index_service.get_document_count(index_name) if exists else 0
            
            return {
                "index_name": index_name,
                "exists": exists,
                "document_count": doc_count,
                "vector_dimensions": settings.VECTOR_DIMENSIONS,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            logger.error(f"Error getting index info: {e}")
            return {
                "index_name": index_name,
                "exists": False,
                "error": str(e)
            }


def run_ingestion_pipeline(
    index_name: Optional[str] = None,
    recreate_index: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run the data ingestion pipeline.
    
    Args:
        index_name: Name of the index (defaults to settings.INDEX_NAME)
        recreate_index: If True, delete and recreate the index if it exists
        
    Returns:
        dict: Pipeline execution results
    """
    pipeline = DataIngestionPipeline()
    return pipeline.run(index_name=index_name, recreate_index=recreate_index)
