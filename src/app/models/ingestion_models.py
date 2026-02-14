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


class IngestionResponse(BaseModel):
    """Response model for data ingestion."""
    success: bool
    message: str
    index_name: str
    index_created: bool
    index_existed: bool
    initial_document_count: int = Field(
        default=0,
        description="Number of documents in index before operation"
    )
    documents_deleted: int = Field(
        default=0,
        description="Number of documents deleted (if index was recreated)"
    )
    documents_fetched: int
    documents_indexed: int
    documents_failed: int
    final_document_count: int = Field(
        default=0,
        description="Number of documents in index after operation"
    )
    errors: list[str]


class IndexInfoResponse(BaseModel):
    """Response model for index information."""
    index_name: str
    exists: bool
    document_count: int
    vector_dimensions: int
    embedding_provider: str
    embedding_model: str
