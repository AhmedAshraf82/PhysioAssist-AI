
from pydantic import BaseModel, Field
from typing import Optional

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
