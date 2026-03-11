"""
Request/Response schemas for API validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from config.constants import MIN_TEXT_LENGTH, MAX_TEXT_LENGTH


class PredictionRequest(BaseModel):
    """Request model for text prediction"""
    
    text: str = Field(
        ...,
        min_length=MIN_TEXT_LENGTH,
        max_length=MAX_TEXT_LENGTH,
        description="Text to classify",
        example="Chaussures de sport Nike homme taille 42"
    )
    
    @validator('text')
    def text_not_empty(cls, v):
        """Ensure text is not just whitespace"""
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v.strip()


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    
    label: int = Field(..., description="Predicted label")
    confidence: Optional[float] = Field(
        None, 
        description="Prediction confidence (0-1)"
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="1.0.0")