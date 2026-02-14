"""
Pydantic models for data ingestion API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class IngestionRequest(BaseModel):
    """Request model for data ingestion."""
    index_name: Optional[str] = Field(
        default=None,
        description="Name of the target index. Defaults to configured INDEX_NAME."
    )
    recreate_index: bool = Field(
        default=True,
        description="Whether to recreate the index if it already exists."
    )


class IndexInfoRequest(BaseModel):
    """Request model for index information query."""
    index_name: Optional[str] = Field(
        default=None,
        description="Name of the index. Defaults to configured INDEX_NAME."
    )


class IngestionResponse(BaseModel):
    """Response model for data ingestion."""
    success: bool
    message: str
    index_name: str
    index_created: bool
    index_existed: bool
    documents_fetched: int
    documents_indexed: int
    documents_failed: int
    errors: list[str]


class IndexInfoResponse(BaseModel):
    """Response model for index information."""
    index_name: str
    exists: bool
    document_count: int
    vector_dimensions: int
    embedding_provider: str
    embedding_model: str


class IndexListResponse(BaseModel):
    """Response model for list of indexes."""
    total_count: int
    indexes: list[str]
    search_service_type: str


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str = Field(
        description="Search query text"
    )


class SearchResult(BaseModel):
    """Individual search result."""
    score: float = Field(description="Relevance score")
    document: dict = Field(description="Document content")


class SearchResponse(BaseModel):
    """Response model for search operations."""
    success: bool
    query: str
    index_name: str
    total_results: int
    results: list[SearchResult]
