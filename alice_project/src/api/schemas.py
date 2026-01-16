from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        example="Chaussures de sport Nike homme taille 42"
    )


class PredictionResponse(BaseModel):
    label: int