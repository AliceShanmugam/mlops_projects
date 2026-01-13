
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import pickle
# ------------------
# Définition de l'API
app = FastAPI(title="Product Category Classification API")

# ------------------
# Chargement du modèle et de l'encodeur
artifact = pickle.load(open("models/model.pkl", "rb"))
model = artifact["model"]
label_encoder = artifact["label_encoder"]

# ------------------
# Définition du format d'entrée
class Item(BaseModel):
    description: str

# ------------------
# Endpoint pour prédiction
@app.post("/predict")
def predict(item: Item):
    text = item.description
    # Prediction
    pred = model.predict([text])
    label = label_encoder.inverse_transform(pred)[0]
    return {"prediction": label}

# Optionnel : endpoint de test
@app.get("/")
def read_root():
    return {"message": "API is running"}