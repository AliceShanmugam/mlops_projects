
# services/gateway/app/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# ---------------- AUTH ----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# ---------------- PREDICTION ----------------
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
