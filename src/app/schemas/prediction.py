"""
Prediction request/response schemas
"""
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request model for predictions"""
    data: dict = Field(..., description="Input data for prediction")
    model_version: str | None = Field(None, description="Specific model version to use")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {"feature1": 1.0, "feature2": 2.0},
                "model_version": "v1"
            }
        }


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction: str | float | dict
    confidence: float | None = None
    message: str | None = None
