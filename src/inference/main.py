# src/inference/main.py

from pathlib import Path
import sys
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from torchvision import transforms
from PIL import Image
import pandas as pd
import logging
import mlflow

# =========================
# CONFIG LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# MLFLOW CONFIG
# =========================
mlflow.set_tracking_uri("https://dagshub.com/Fouxy84/mlops_projects.mlflow")

# =========================
# PATHS
# =========================
IN_DOCKER = Path("/app").exists()
BASE_DIR = Path("/app") if IN_DOCKER else Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

# =========================
# LOAD LABELS
# =========================
try:
    df_labels = pd.read_csv(DATA_PROCESSED_DIR / "train_clean.csv")
    label_mapping = (
        df_labels[["label", "label_name"]]
        .drop_duplicates()
        .set_index("label")["label_name"]
    )
    LABEL_ID_TO_NAME = label_mapping.to_dict()
except Exception as e:
    logger.warning(f"Labels fallback: {e}")
    LABEL_ID_TO_NAME = {i: f"Label_{i}" for i in range(8)}

# =========================
# CONFIG IMAGE
# =========================
DEVICE = torch.device("cpu")
IMAGE_SIZE = 128

transform = transforms.Compose(
    [
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5] * 3, std=[0.5] * 3),
    ]
)

# =========================
# GLOBAL MODELS
# =========================
text_model = None
image_model = None


# =========================
# LOAD MODELS (MLFLOW FIRST)
# =========================
def load_text_model():
    try:
        model = mlflow.pyfunc.load_model(
            model_uri="models:/Text_Classifier_SVM/Production"
        )
        logger.info("✅ Text model loaded from MLflow")
        return model
    except Exception as e:
        logger.error(f"MLflow text load failed: {e}")
        return None


def load_image_model():
    try:
        model = mlflow.pyfunc.load_model(
            model_uri="models:/CNN_Image_Classifier/Production"
        )
        logger.info("✅ Image model loaded from MLflow")
        return model
    except Exception as e:
        logger.error(f"MLflow image load failed: {e}")
        return None


# =========================
# FASTAPI
# =========================
app = FastAPI(
    title="MLOps Inference API (MLflow)",
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
# HEALTH
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# PREDICT TEXT
# =========================
@app.post("/predict/svm", response_model=PredictResponse)
def predict_svm(request: PredictTextRequest):

    if text_model is None:
        raise HTTPException(503, "Text model not loaded")

    try:
        import pandas as pd

        df = pd.DataFrame({"text": [request.text]})
        pred = text_model.predict(df)[0]

        return {
            "predicted_label": int(pred),
            "label_name": LABEL_ID_TO_NAME.get(pred, "unknown"),
        }

    except Exception as e:
        logger.error(f"SVM error: {e}")
        raise HTTPException(500, str(e))


# =========================
# PREDICT IMAGE
# =========================
@app.post("/predict/cnn", response_model=PredictResponse)
def predict_cnn(request: PredictImageRequest):

    if image_model is None:
        raise HTTPException(503, "Image model not loaded")

    try:
        image_path = Path(request.image_path)
        if not image_path.is_absolute():
            image_path = BASE_DIR / "data/raw/image_train" / image_path.name

        image = Image.open(image_path).convert("RGB")
        tensor = transform(image).unsqueeze(0)

        import pandas as pd

        df = pd.DataFrame({"image": [tensor.numpy().tolist()]})

        pred = image_model.predict(df)[0]

        return {
            "predicted_label": int(pred),
            "label_name": LABEL_ID_TO_NAME.get(pred, "unknown"),
        }

    except Exception as e:
        logger.error(f"CNN error: {e}")
        raise HTTPException(500, str(e))


# =========================
# RELOAD ENDPOINTS
# =========================
@app.post("/reload/text")
def reload_text():
    global text_model
    text_model = load_text_model()
    return {"status": "text_model_reloaded"}


@app.post("/reload/image")
def reload_image():
    global image_model
    image_model = load_image_model()
    return {"status": "image_model_reloaded"}


# =========================
# INFO
# =========================
@app.get("/info/text")
def info_text():
    return {"model": "Text_Classifier_SVM", "source": "MLflow"}


@app.get("/info/image")
def info_image():
    return {"model": "CNN_Image_Classifier", "source": "MLflow"}


# =========================
# STARTUP
# =========================
@app.on_event("startup")
def startup():
    global text_model, image_model

    logger.info("🚀 Loading models from MLflow...")

    text_model = load_text_model()
    image_model = load_image_model()

    if text_model is None:
        logger.warning("⚠️ Text model not loaded")

    if image_model is None:
        logger.warning("⚠️ Image model not loaded")

    logger.info("✅ Inference API ready")
