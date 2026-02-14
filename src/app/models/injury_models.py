"""
Pydantic models for injury API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class InjuryCreate(BaseModel):
    """Request model for creating an injury."""
    title: str = Field(description="Title of the injury")
    content: str = Field(description="Detailed content about the injury")
    tags: list[str] = Field(description="List of tags for categorization")


class InjuryUpdate(BaseModel):
    """Request model for updating an injury."""
    content: Optional[str] = Field(default=None, description="Updated content")
    tags: Optional[list[str]] = Field(default=None, description="Updated tags")


class InjuryResponse(BaseModel):
    """Response model for injury operations."""
    title: str
    content: str
    tags: list[str]


class InjuryCreateResponse(BaseModel):
    """Response model for injury creation."""
    success: bool
    message: str
    injury_id: str


class InjuryOperationResponse(BaseModel):
    """Response model for injury operations (update/delete)."""
    success: bool
    message: str


class InjuryListResponse(BaseModel):
    """Response model for list of injuries."""
    success: bool
    count: int
    injuries: list[InjuryResponse]


class InjuryCountResponse(BaseModel):
    """Response model for injury count."""
    count: int
    collection_name: str
