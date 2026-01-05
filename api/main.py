
from pathlib import Path
import joblib
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from torchvision import transforms
from PIL import Image

from src.models.train_cnn import SimpleCNN

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

TEXT_MODELS_DIR = BASE_DIR / "models/text"
IMAGE_MODELS_DIR = BASE_DIR / "models/images"

# =========================
# LOAD TEXT MODEL
# =========================
tfidf = joblib.load(TEXT_MODELS_DIR / "tfidf.joblib")
svm = joblib.load(TEXT_MODELS_DIR / "svm.joblib")

# =========================
# LOAD CNN MODEL
# =========================
NUM_CLASSES = 8
DEVICE = torch.device("cpu")

cnn_model = SimpleCNN(NUM_CLASSES)
cnn_model.load_state_dict(
    torch.load(IMAGE_MODELS_DIR / "cnn.pt", map_location=DEVICE)
)
cnn_model.to(DEVICE)
cnn_model.eval()

# =========================
# IMAGE TRANSFORM
# =========================
IMAGE_SIZE = 128

transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3),
])

# =========================
# FASTAPI
# =========================
app = FastAPI(
    title="Rakuten MLOps Inference API",
    description="Text + Image classification"
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
    decision_score: Optional[list[float]] = None

# =========================
# ENDPOINTS
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict/svm", response_model=PredictResponse)
def predict_svm(request: PredictTextRequest):
    X = tfidf.transform([request.text])
    pred = svm.predict(X)[0]

    response = {"predicted_label": int(pred)}
    if hasattr(svm, "decision_function"):
        response["decision_score"] = svm.decision_function(X)[0].tolist()

    return response

@app.post("/predict/cnn", response_model=PredictResponse)
def predict_cnn(request: PredictImageRequest):
    try:
        image_path = Path(request.image_path)

        if not image_path.is_absolute():
            image_path = BASE_DIR / image_path

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        image = Image.open(image_path).convert("RGB")
        tensor = transform(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = cnn_model(tensor)
            pred = outputs.argmax(dim=1).item()

        return {"predicted_label": pred}

    except Exception as e:
        print("❌ CNN inference error:", e)
        raise HTTPException(status_code=500, detail=str(e))
