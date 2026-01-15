# src/inference/main.py
 
from pathlib import Path
import sys
import joblib
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from torchvision import transforms
from PIL import Image
import pandas as pd
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# CONFIGURATION DES CHEMINS
# =========================
IN_DOCKER = Path("/app").exists()
BASE_DIR = Path("/app") if IN_DOCKER else Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

TEXT_MODELS_DIR = BASE_DIR / "models" / "text"
IMAGE_MODELS_DIR = BASE_DIR / "models" / "images"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

# =========================
# CHARGER LABELS
# =========================
try:
    df_labels = pd.read_csv(DATA_PROCESSED_DIR / "train_clean.csv")
    # Créer un mapping unique: label_id -> label_name
    label_mapping = df_labels[['label', 'label_name']].drop_duplicates().set_index('label')['label_name']
    LABEL_ID_TO_NAME = label_mapping.to_dict()
    logger.info(f"Labels chargés: {len(LABEL_ID_TO_NAME)} classes")
except Exception as e:
    logger.warning(f"Impossible de charger les labels: {e}")
    LABEL_ID_TO_NAME = {i: f"Label_{i}" for i in range(8)}

# =========================
# IMPORT MODÈLE CNN
# =========================
from src.train_models.train_cnn import SimpleCNN

# =========================
# CONFIGURATION MODÈLES
# =========================
NUM_CLASSES = 8
DEVICE = torch.device("cpu")
IMAGE_SIZE = 128

# Transforms pour les images
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3),
])

# =========================
# CHARGEMENT GRACIEUX DES MODÈLES
# =========================
text_model = None
image_model = None

def load_text_model_from_local() -> Optional[tuple]:
    try:
        tfidf_path = TEXT_MODELS_DIR / "tfidf.joblib"
        svm_path = TEXT_MODELS_DIR / "svm.joblib"
        
        if not tfidf_path.exists() or not svm_path.exists():
            raise FileNotFoundError(f"Modèles texte introuvables dans {TEXT_MODELS_DIR}")
        
        tfidf = joblib.load(tfidf_path)
        svm = joblib.load(svm_path)
        logger.info("Modèle texte (SVM + TF-IDF) chargé depuis fichiers locaux")
        return (tfidf, svm)
    except Exception as e:
        logger.error(f"Impossible de charger le modèle texte: {e}")
        return None

def load_image_model_from_local() -> Optional[torch.nn.Module]:
    try:
        cnn_path = IMAGE_MODELS_DIR / "cnn.pt"
        
        if not cnn_path.exists():
            raise FileNotFoundError(f"Modèle image introuvable: {cnn_path}")
        
        cnn = SimpleCNN(NUM_CLASSES)
        cnn.load_state_dict(torch.load(cnn_path, map_location=DEVICE))
        cnn.to(DEVICE)
        cnn.eval()
        logger.info("Modèle image (CNN) chargé depuis fichier local")
        return cnn
    except Exception as e:
        logger.error(f"Impossible de charger le modèle image: {e}")
        return None

# =========================
# FASTAPI
# =========================
app = FastAPI(
    title="Rakuten MLOps Inference API",
    description="API pour la classification texte et images"
)

class PredictTextRequest(BaseModel):
    text: str

class PredictImageRequest(BaseModel):
    image_path: str

class PredictResponse(BaseModel):
    predicted_label: int
    label_name: str
    decision_score: Optional[List[float]] = None

# =========================
# ENDPOINTS
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict/svm", response_model=PredictResponse)
def predict_svm(request: PredictTextRequest):
    if text_model is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle texte non disponible. Entrainez d'abord le modèle."
        )
    
    try:
        tfidf, svm = text_model
        X = tfidf.transform([request.text])
        pred = svm.predict(X)[0]
        decision = svm.decision_function(X)[0].tolist()
        
        return {
            "predicted_label": int(pred),
            "label_name": LABEL_ID_TO_NAME.get(pred, "unknown"),
            "decision_score": decision if isinstance(decision, list) else [decision]
        }
    except Exception as e:
        logger.error(f"Erreur prédiction SVM: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur prédiction: {str(e)}")

@app.post("/predict/cnn", response_model=PredictResponse)
def predict_cnn(request: PredictImageRequest):
    if image_model is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle image non disponible. Entrainez d'abord le modèle."
        )
    
    try:
        image_path = Path(request.image_path)
        if not image_path.is_absolute():
            image_path = BASE_DIR / "data" / "raw" / "image_train" / image_path.name
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image non trouvée: {image_path}")
        
        image = Image.open(image_path).convert("RGB")
        tensor = transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            outputs = image_model(tensor)
            pred = outputs.argmax(dim=1).item()
            probs = torch.softmax(outputs, dim=1).squeeze().tolist()
        
        return {
            "predicted_label": int(pred),
            "label_name": LABEL_ID_TO_NAME.get(pred, "unknown"),
            "decision_score": probs if isinstance(probs, list) else [probs]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur prédiction CNN: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur prédiction: {str(e)}")

# =========================
# DÉMARRAGE APPLICATION
# =========================
@app.on_event("startup")
async def startup_event():
    global text_model, image_model
    
    logger.info("Démarrage de l'application d'inférence...")
    
    # Charger modèle texte
    text_model = load_text_model_from_local()
    if text_model is None:
        logger.warning("Modèle texte non disponible - prédictions SVM désactivées")
    
    # Charger modèle image
    image_model = load_image_model_from_local()
    if image_model is None:
        logger.warning("Modèle image non disponible - prédictions CNN désactivées")
    
    if text_model is None and image_model is None:
        logger.warning("ATTENTION: Aucun modèle n'a pu être chargé!")
    else:
        logger.info("Application prête pour les prédictions")

    