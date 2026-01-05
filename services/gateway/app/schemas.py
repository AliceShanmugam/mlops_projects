# services/gateway/app/schemas.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from pathlib import Path


# ======================================================
# AUTH
# ======================================================
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# ======================================================
# TEXT PREDICTION (SVM)
# ======================================================
class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Texte du produit à classifier",
        examples=["Ordinateur portable 15 pouces, 8GB RAM, SSD 256GB"],
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le texte ne peut pas être vide")
        if len(v) > 10000:
            raise ValueError("Le texte ne peut pas dépasser 10000 caractères")
        return v


# ======================================================
# IMAGE PREDICTION (CNN)
# ======================================================
class PredictImageRequest(BaseModel):
    image_path: str = Field(
        ...,
        description="Chemin vers l’image à classifier (chemin relatif ou absolu)",
        examples=["data/raw/image_train/image_528113_product_923222.jpg"],
    )

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le chemin de l’image ne peut pas être vide")

        # sécurité minimale : pas d’URL, pas de schéma
        if v.startswith(("http://", "https://")):
            raise ValueError("Les URLs ne sont pas autorisées, chemin local uniquement")

        # extension
        if not v.lower().endswith((".jpg", ".jpeg", ".png")):
            raise ValueError("Format d’image non supporté (jpg, jpeg, png uniquement)")

        return v
