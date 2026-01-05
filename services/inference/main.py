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
# Load TEXT model
# =========================
TEXT_DIR = Path("/models/text")
tfidf = joblib.load(TEXT_DIR / "tfidf.joblib")
svm = joblib.load(TEXT_DIR / "svm.joblib")

# =========================
# Load IMAGE model
# =========================
IMG_DIR = Path("/models/images")
cnn = SimpleCNN(num_classes=8)
cnn.load_state_dict(torch.load(IMG_DIR / "cnn.pt", map_location="cpu"))
cnn.eval()

transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3),
])

# =========================
# FastAPI
# =========================
app = FastAPI(title="Inference Service")

class TextRequest(BaseModel):
    text: str

class ImageRequest(BaseModel):
    image_path: str

class PredictResponse(BaseModel):
    predicted_label: int
    decision_score: Optional[list[float]] = None



@app.get("/health")
def health():
    return {"status": "ok", "service": "inference"}



@app.post("/predict/svm", response_model=PredictResponse)
def predict_svm(req: TextRequest):
    X = tfidf.transform([req.text])
    pred = svm.predict(X)[0]

    response = {"predicted_label": int(pred)}
    if hasattr(svm, "decision_function"):
        response["decision_score"] = svm.decision_function(X)[0].tolist()

    return response


@app.post("/predict/cnn", response_model=PredictResponse)
def predict_cnn(req: ImageRequest):
    img_path = Path(req.image_path)

    if not img_path.exists():
        raise HTTPException(404, "Image not found")

    img = Image.open(img_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        outputs = cnn(tensor)
        pred = outputs.argmax(dim=1).item()

    return {"predicted_label": pred}
