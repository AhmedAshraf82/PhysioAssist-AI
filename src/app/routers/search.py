"""
Search API endpoints.
Provides hybrid search functionality using RAG service.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from src.app.services.rag_service import RAGService
from src.app.models.ingestion_models import SearchRequest, SearchResponse, SearchResult
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse, summary="Hybrid search in vector store")
async def search(request: SearchRequest) -> SearchResponse:
    """
    Perform hybrid search combining BM25 full-text search and vector similarity search.
    
    Hybrid search provides the best of both worlds:
    - BM25: Keyword matching with term frequency scoring
    - Vector: Semantic similarity using embeddings
    
    Args:
        request: Search configuration
        
    Returns:
        SearchResponse: Search results with scores and documents
        
    Example:
        ```json
        POST /search/
        {
            "query": "neck pain and numbness in arm"
        }
        ```
    """
    # Use default values
    index_name = settings.INDEX_NAME
    text_fields = ["title", "content", "tags",]
    size = 5
    
    logger.info("="*80)
    logger.info("Search API Endpoint Called")
    logger.info("="*80)
    logger.info(f"Query: {request.query}")
    logger.info(f"Index: {index_name}")
    logger.info(f"Size: {size}")
    logger.info(f"Text fields: {text_fields}")
    
    try:
        # Initialize RAG service
        rag_service = RAGService(search_service_type=settings.SEARCH_SERVICE_TYPE)
        
        # Perform hybrid search
        results = rag_service.hybrid_search(
            index_name=index_name,
            query=request.query,
            text_fields=text_fields,
            vector_field="embedding",
            text_weight=0.2,
            vector_weight=0.8,
            size=size
        )
        
        logger.info(f"Found {len(results)} results")
        
        # Format results
        search_results = [
            SearchResult(
                score=result.get("score", 0.0),
                document=result.get("source", {})
            )
            for result in results
        ]
        
        return SearchResponse(
            success=True,
            query=request.query,
            index_name=index_name,
            total_results=len(search_results),
            results=search_results
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/health", summary="Search service health check")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for search service.
    
    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "search",
        "search_service_type": settings.SEARCH_SERVICE_TYPE,
        "default_index": settings.INDEX_NAME
    }
