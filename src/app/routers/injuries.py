"""
Injury management API endpoints.
Provides CRUD operations for physiotherapy injury documents.
"""

from fastapi import APIRouter, HTTPException, Path
from typing import List
from src.app.services.db_handler.injury_handler import InjuryHandler
from src.app.models.injury_models import (
    InjuryCreate,
    InjuryUpdate,
    InjuryResponse,
    InjuryCreateResponse,
    InjuryOperationResponse,
    InjuryListResponse,
    InjuryCountResponse
)
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/injuries", tags=["Injuries"])


@router.get("/", response_model=InjuryListResponse, summary="Get all injuries")
async def get_all_injuries() -> InjuryListResponse:
    """
    Retrieve all injury documents from MongoDB.
    
    Returns all injuries formatted for use in the RAG pipeline.
    
    Returns:
        InjuryListResponse: List of all injury documents
    """
    logger.info("Fetching all injuries")
    
    try:
        with InjuryHandler() as handler:
            injuries = handler.get_all_injuries()
        
        logger.info(f"Retrieved {len(injuries)} injuries")
        
        return InjuryListResponse(
            success=True,
            count=len(injuries),
            injuries=injuries
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve injuries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve injuries: {str(e)}"
        )


@router.post("/", response_model=InjuryCreateResponse, summary="Create new injury")
async def create_injury(injury: InjuryCreate) -> InjuryCreateResponse:
    """
    Add a new injury document to MongoDB.
    
    Args:
        injury: Injury data (title, content, tags)
        
    Returns:
        InjuryCreateResponse: Created injury ID and status
        
    Example:
        ```json
        POST /injuries/
        {
            "title": "Tennis Elbow",
            "content": "Overuse injury of the elbow...",
            "tags": ["elbow", "overuse", "tendinitis"]
        }
        ```
    """
    logger.info(f"Creating injury: {injury.title}")
    
    try:
        with InjuryHandler() as handler:
            injury_id = handler.add_injury(injury.model_dump())
        
        logger.info(f"Created injury: {injury.title} (ID: {injury_id})")
        
        return InjuryCreateResponse(
            success=True,
            message=f"Injury '{injury.title}' created successfully",
            injury_id=injury_id
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create injury: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create injury: {str(e)}"
        )


@router.get("/count", response_model=InjuryCountResponse, summary="Get injury count")
async def get_injury_count() -> InjuryCountResponse:
    """
    Get the total count of injuries in the collection.
    
    Returns:
        InjuryCountResponse: Total count of injuries
    """
    logger.info("Getting injury count")
    
    try:
        with InjuryHandler() as handler:
            count = handler.count_injuries()
        
        return InjuryCountResponse(
            count=count,
            collection_name=settings.MONGODB_COLLECTION_NAME
        )
        
    except Exception as e:
        logger.error(f"Failed to count injuries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to count injuries: {str(e)}"
        )


@router.get("/tag/{tag}", response_model=InjuryListResponse, summary="Get injuries by tag")
async def get_injuries_by_tag(
    tag: str = Path(description="Tag to filter by")
) -> InjuryListResponse:
    """
    Retrieve injuries filtered by a specific tag.
    
    Args:
        tag: Tag to filter by (e.g., "neck", "shoulder", "knee")
        
    Returns:
        InjuryListResponse: List of matching injuries
    """
    logger.info(f"Fetching injuries with tag: {tag}")
    
    try:
        with InjuryHandler() as handler:
            injuries = handler.get_injuries_by_tag(tag)
        
        logger.info(f"Found {len(injuries)} injuries with tag '{tag}'")
        
        return InjuryListResponse(
            success=True,
            count=len(injuries),
            injuries=injuries
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve injuries by tag: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve injuries by tag: {str(e)}"
        )


@router.get("/{title}", response_model=InjuryResponse, summary="Get injury by title")
async def get_injury_by_title(
    title: str = Path(description="Title of the injury")
) -> InjuryResponse:
    """
    Retrieve a specific injury by its title.
    
    Args:
        title: Exact title of the injury to find
        
    Returns:
        InjuryResponse: Injury document
    """
    logger.info(f"Fetching injury: {title}")
    
    try:
        with InjuryHandler() as handler:
            injury = handler.get_injury_by_title(title)
        
        if not injury:
            raise HTTPException(
                status_code=404,
                detail=f"Injury not found: {title}"
            )
        
        return InjuryResponse(**injury)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve injury: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve injury: {str(e)}"
        )


@router.put("/{title}", response_model=InjuryOperationResponse, summary="Update injury")
async def update_injury(
    title: str = Path(description="Title of the injury to update"),
    update_data: InjuryUpdate = None
) -> InjuryOperationResponse:
    """
    Update an existing injury document.
    
    Args:
        title: Title of the injury to update
        update_data: Fields to update (content, tags)
        
    Returns:
        InjuryOperationResponse: Success status and message
    """
    logger.info(f"Updating injury: {title}")
    
    try:
        # Filter out None values
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )
        
        with InjuryHandler() as handler:
            success = handler.update_injury(title, update_dict)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Injury not found: {title}"
            )
        
        return InjuryOperationResponse(
            success=True,
            message=f"Injury '{title}' updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update injury: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update injury: {str(e)}"
        )


@router.delete("/{title}", response_model=InjuryOperationResponse, summary="Delete injury")
async def delete_injury(
    title: str = Path(description="Title of the injury to delete")
) -> InjuryOperationResponse:
    """
    Delete an injury document by title.
    
    Args:
        title: Title of the injury to delete
        
    Returns:
        InjuryOperationResponse: Success status and message
    """
    logger.info(f"Deleting injury: {title}")
    
    try:
        with InjuryHandler() as handler:
            success = handler.delete_injury(title)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Injury not found: {title}"
            )
        
        return InjuryOperationResponse(
            success=True,
            message=f"Injury '{title}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete injury: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete injury: {str(e)}"
        )


@router.get("/health/status", summary="Injury service health check")
async def health_check():
    """
    Health check endpoint for injury management service.
    
    Returns:
        dict: Service health status and configuration
    """
    return {
        "status": "healthy",
        "service": "injury-management",
        "database": settings.MONGODB_DATABASE_NAME,
        "collection": settings.MONGODB_COLLECTION_NAME
    }
