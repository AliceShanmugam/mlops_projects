from pathlib import Path
from typing import Optional, List

import joblib
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from torchvision import transforms
from PIL import Image

from src.models.train_cnn import SimpleCNN


# =========================
# PATHS & CONSTANTS
# =========================
ARTIFACTS_TEXT_DIR = Path("models/run_linear_svm2")
ARTIFACTS_IMAGE_DIR = Path("models/images")

NUM_CLASSES = 8
IMAGE_SIZE = 224
DEVICE = "cpu"


# =========================
# LOAD TEXT MODEL (SVM)
# =========================
tfidf = joblib.load(ARTIFACTS_TEXT_DIR / "tfidf.joblib")
svm = joblib.load(ARTIFACTS_TEXT_DIR / "svm.joblib")


# =========================
# LOAD IMAGE MODEL (CNN)
# =========================
cnn_model = SimpleCNN(NUM_CLASSES)
cnn_state = torch.load(ARTIFACTS_IMAGE_DIR / "cnn.pt", map_location=DEVICE)
cnn_model.load_state_dict(cnn_state)
cnn_model.eval()


# =========================
# IMAGE TRANSFORM
# =========================
image_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])


# =========================
# FASTAPI APP
# =========================
app = FastAPI(
    title="Rakuten MLOps Inference API",
    description="Inference API for text (SVM) and image (CNN) classification",
)


# =========================
# SCHEMAS
# =========================
class PredictTextRequest(BaseModel):
    text: str


class PredictImageRequest(BaseModel):
    image_path: str


class PredictResponse(BaseModel):
    predicted_label: int
    decision_score: Optional[List[float]] = None


# =========================
# ENDPOINTS
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}


# -------- TEXT / SVM --------
@app.post("/predict/svm", response_model=PredictResponse)
def predict_svm(request: PredictTextRequest):
    X = tfidf.transform([request.text])
    pred = svm.predict(X)[0]

    response = {"predicted_label": int(pred)}

    if hasattr(svm, "decision_function"):
        scores = svm.decision_function(X)
        response["decision_score"] = scores[0].tolist()

    return response


# -------- IMAGE / CNN --------
@app.post("/predict/cnn", response_model=PredictResponse)
def predict_cnn(request: PredictImageRequest):
    image_path = Path(request.image_path)

    # Resolve relative path
    if not image_path.is_absolute():
        image_path = Path.cwd() / image_path

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    image = Image.open(image_path).convert("RGB")
    tensor = image_transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = cnn_model(tensor)
        pred = outputs.argmax(dim=1).item()

    return {"predicted_label": pred}
