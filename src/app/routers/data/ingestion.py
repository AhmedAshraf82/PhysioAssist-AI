"""
Data ingestion API endpoints.
Handles data ingestion pipeline execution and index management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from src.app.services.data_ingestion_pipeline import DataIngestionPipeline
from src.app.models.ingestion_models import (
    IngestionRequest,
    IngestionResponse,
    IndexInfoResponse
)
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/data", tags=["Data Ingestion"])


@router.post("/ingest", response_model=IngestionResponse, summary="Ingest data into vector store")
async def ingest_data(request: IngestionRequest) -> IngestionResponse:
    """
    Run the data ingestion pipeline to index documents into the vector store.
    
    This endpoint:
    1. Creates or verifies the target index
    2. Fetches documents from the data source (currently sample data, MongoDB in future)
    3. Generates embeddings for all documents
    4. Indexes documents into the vector store
    
    Args:
        request: Ingestion configuration
        
    Returns:
        IngestionResponse: Pipeline execution results with statistics
        
    Example:
        ```json
        POST /data/ingest
        {
            "index_name": "physio_injuries",
            "recreate_index": true
        }
        ```
    """
    logger.info("="*80)
    logger.info("Data Ingestion API Endpoint Called")
    logger.info("="*80)
    logger.info(f"Request: index_name={request.index_name}, recreate={request.recreate_index}")
    
    try:
        # Initialize pipeline
        pipeline = DataIngestionPipeline(
            search_service_type=settings.SEARCH_SERVICE_TYPE,
            embedding_provider=settings.EMBEDDING_PROVIDER,
            embedding_model=settings.EMBEDDING_MODEL
        )
        
        # Run pipeline
        results = pipeline.run(
            index_name=request.index_name,
            recreate_index=request.recreate_index
        )
        
        logger.info(f"Pipeline completed: success={results['success']}")
        logger.info(f"Documents: fetched={results['documents_fetched']}, indexed={results['documents_indexed']}, failed={results['documents_failed']}")
        
        return IngestionResponse(**results)
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Data ingestion failed: {str(e)}"
        )


@router.get("/index-info", response_model=IndexInfoResponse, summary="Get index information")
async def get_index_info(
    index_name: Optional[str] = Query(
        default=None,
        description="Name of the index. Defaults to configured INDEX_NAME."
    )
) -> IndexInfoResponse:
    """
    Get information about a vector store index.
    
    Returns details about the index including:
    - Whether it exists
    - Number of documents
    - Vector dimensions
    - Embedding configuration
    
    Args:
        index_name: Name of the index to query
        
    Returns:
        IndexInfoResponse: Index information and statistics
    """
    logger.info(f"Getting index info for: {index_name or settings.INDEX_NAME}")
    
    try:
        pipeline = DataIngestionPipeline()
        info = pipeline.get_index_info(index_name=index_name)
        
        if "error" in info:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get index info: {info['error']}"
            )
        
        return IndexInfoResponse(**info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get index info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get index info: {str(e)}"
        )


@router.get("/health", summary="Data service health check")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for data ingestion service.
    
    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "data-ingestion",
        "search_service": settings.SEARCH_SERVICE_TYPE,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "default_index": settings.INDEX_NAME
    }
