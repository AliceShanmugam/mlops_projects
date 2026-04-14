"""
Request/Response schemas for API validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from config.constants import MIN_TEXT_LENGTH, MAX_TEXT_LENGTH


class TextPredictionRequest(BaseModel):
    """Request model for text prediction"""
    
    text: str = Field(
        ...,
        min_length=MIN_TEXT_LENGTH,
        max_length=MAX_TEXT_LENGTH,
        description="Text to classify",
        example="Chaussures de sport Nike homme taille 42"
    )
    
    def text_not_empty(cls, v):
        """Ensure text is not just whitespace"""
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v.strip()


class ImagePredictionRequest(BaseModel):
    image_path: str = Field(
        ...,
        description="Chemin local vers l'image produit",
        example="/app/data/images/product_123.jpg",
    )


class CombinedPredictionRequest(BaseModel):
    """Requête combinée texte + image (les deux optionnels mais au moins un requis)."""
    text: Optional[str] = Field(None, min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)
    image_path: Optional[str] = Field(None)

    def text_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v.strip() if v else v

    def at_least_one_input(cls, image_path, values):
        if not values.get("text") and not image_path:
            raise ValueError("Au moins 'text' ou 'image_path' est requis")
        return image_path


class PredictionResponse(BaseModel):
    label: int = Field(..., description="Label prédit (0-7)")
    source: str = Field(..., description="Modèle(s) utilisé(s): 'text', 'image', 'combined'")
    text_label: Optional[int] = Field(None, description="Prédiction texte seule")
    image_label: Optional[int] = Field(None, description="Prédiction image seule")
    fallback: bool = Field(False, description="True si un modèle a échoué")
    fallback_reason: Optional[str] = Field(None)


# Garde la compatibilité avec le code existant
PredictionRequest = TextPredictionRequest


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="1.0.0")