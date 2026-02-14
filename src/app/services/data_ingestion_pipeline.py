"""
Data ingestion pipeline for indexing documents into vector stores.
Orchestrates the complete flow: index creation -> data fetching -> embedding -> indexing.
"""

from typing import Dict, Any, Optional, List
from src.app.models.injury_models import InjuryListResponse
from src.app.services.db_handler.injury_handler import InjuryHandler
from src.app.services.index_creation import IndexCreationService
from src.app.services.indexer import IndexerService
from src.app.vectorstores.sample_data import get_sample_documents
from src.app.core.config import settings
from src.app.utils.logger import setup_logger
from fastapi import HTTPException

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
            text_fields = ["title", "content", "tags"]
        
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
            "documents_fetched": 0,
            "documents_indexed": 0,
            "documents_failed": 0,
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
                if recreate_index:
                    logger.info(f"Index '{index_name}' exists. Recreating...")
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
            try:
                with InjuryHandler() as handler:
                    injuries = handler.get_all_injuries()
                    
                if not injuries:
                    error_msg = "No injuries found in MongoDB. Please populate the injuries collection first."
                    logger.error(f"✗ {error_msg}")
                    results["errors"].append(error_msg)
                    results["message"] = error_msg
                    return results
                    
                logger.info(f"✓ Retrieved {len(injuries)} injuries from MongoDB")
                documents = injuries
                results["documents_fetched"] = len(documents)
                
            except Exception as e:
                error_msg = f"Failed to retrieve injuries from MongoDB: {str(e)}"
                logger.error(f"✗ {error_msg}")
                results["errors"].append(error_msg)
                results["message"] = error_msg
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
            doc_count = index_service.get_document_count(index_name)
            logger.info(f"✓ Final document count in index: {doc_count}")
            
            # Determine success
            if results["documents_indexed"] == results["documents_fetched"]:
                results["success"] = True
                results["message"] = f"Successfully ingested {results['documents_indexed']} documents"
                logger.info("✓ Data ingestion completed successfully!")
            elif results["documents_indexed"] > 0:
                results["success"] = True
                results["message"] = f"Partially successful: {results['documents_indexed']}/{results['documents_fetched']} documents indexed"
                logger.warning(f"⚠️  Partial success: {results['documents_indexed']}/{results['documents_fetched']} documents indexed")
            else:
                results["message"] = "Failed to index any documents"
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


    def list_all_indexes(self) -> List[str]:
        """
        List all indexes in the search service.
        
        Returns:
            List[str]: List of all index names
        """
        try:
            index_service = IndexCreationService(search_service_type=self.search_service_type)
            indexes = index_service.list_indexes()
            logger.info(f"Found {len(indexes)} indexes")
            return indexes
        except Exception as e:
            logger.error(f"Error listing indexes: {e}")
            return []


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
