# src/inference/main.py

# from pathlib import Path
# import sys
# import joblib
# import torch
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Optional, List
# from torchvision import transforms
# from PIL import Image
# import pandas as pd
# import mlflow
# import mlflow.pyfunc
# import mlflow.pytorch

# # =========================
# # CONFIGURATION DES CHEMINS
# # =========================
# IN_DOCKER = Path("/app").exists()
# BASE_DIR = Path("/app") if IN_DOCKER else Path(__file__).resolve().parent.parent.parent


# # MODELS_DIR = Path("app/src/mlflow/mlruns")
# # TEXT_MODELS_DIR = MODELS_DIR 
# # IMAGE_MODELS_DIR = MODELS_DIR
# LABEL_NAME_DIR = BASE_DIR /"data" / "processed" 
# df_labels = pd.read_csv(LABEL_NAME_DIR / "train_clean.csv")
# LABEL_ID_TO_NAME = (df_labels.set_index("label")["label_name"].to_dict())

# # =========================
# # IMPORT DES MODÈLES
# # =========================
# from src.train_models.train_cnn import SimpleCNN

# # =========================
# # CHARGEMENT DES MODÈLES
# # =========================
# # Modèle texte (SVM + TF-IDF)
# # tfidf = joblib.load(TEXT_MODELS_DIR / "tfidf.joblib")
# # svm = joblib.load(TEXT_MODELS_DIR / "svm.joblib")

# # # Modèle image (CNN)
# # NUM_CLASSES = 8

# # cnn_model = SimpleCNN(NUM_CLASSES)
# # cnn_model.load_state_dict(torch.load(IMAGE_MODELS_DIR / "cnn.pt", map_location=DEVICE))

# mlflow.set_tracking_uri("http://mlflow:5000")
# TEXT_MODEL_URI = "models:/Text_Classifier_SVM/Production"
# IMAGE_MODEL_URI = "models:/Image_Classifier_CNN/Production"

# text_model = mlflow.pyfunc.load_model(TEXT_MODEL_URI)
# cnn_model = mlflow.pytorch.load_model(IMAGE_MODEL_URI)

# DEVICE = torch.device("cpu")
# cnn_model.to(DEVICE)
# cnn_model.eval()

# # =========================
# # TRANSFORMS POUR LES IMAGES
# # =========================
# IMAGE_SIZE = 128
# transform = transforms.Compose([
#     transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.5]*3, std=[0.5]*3),
# ])

# # =========================
# # FASTAPI 
# # =========================
# app = FastAPI(
#     title="Rakuten MLOps Inference API",
#     description="API pour la classification multimodale texte et images"
# )

# class PredictTextRequest(BaseModel):
#     text: str

# class PredictImageRequest(BaseModel):
#     image_path: str

# class PredictResponse(BaseModel):
#     predicted_label: int
#     label_name : str
#     decision_score: Optional[List[float]] = None

# @app.get("/health")
# def health():
#     return {"status": "ok"}

# @app.post("/predict/svm",response_model = PredictResponse)
# def predict_svm(request: PredictTextRequest):
#     #X = tfidf.transform([request.text])
#     pred = text_model.predict([request.text])[0]
#     response = {
#         "predicted_label": int(pred),
#         "label_name":LABEL_ID_TO_NAME.get(pred,"unknown"),
#         "decision_score" : text_model.decision_function(request.text)[0].tolist()}
#     return response

# @app.post("/predict/cnn",response_model=PredictResponse)
# def predict_cnn(request: PredictImageRequest):
#         image_path = Path(request.image_path)
#         if not image_path.is_absolute():
#             image_path = BASE_DIR / "data" / "raw" / "image_train" / image_path.name
        
#         if not image_path.exists():
#             raise HTTPException(status_code=404, detail=f"Image non trouvée : {image_path}")
        
#         image = Image.open(image_path).convert("RGB")
#         tensor = transform(image).unsqueeze(0).to(DEVICE)
        
#         with torch.no_grad():
#             outputs = cnn_model(tensor)
#             pred = outputs.argmax(dim=1).item()
#         return {
#             "predicted_label": pred,
#             "label_name":LABEL_ID_TO_NAME.get(pred,"unknown"), 
#             "decision_score": torch.softmax(outputs, dim=1).squeeze().tolist()}
    
from fastapi import FastAPI, BackgroundTasks, HTTPException
import mlflow
from mlflow.tracking import MlflowClient
import logging
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rakuten Training Service")

# =========================
# UTILITAIRES MLFLOW
# =========================
def load_mlflow_model(model_name: str, stage: str = "Production") -> Any:
    """Charge un modèle depuis MLflow avec gestion d'erreur."""
    client = MlflowClient()
    try:
        # Vérifie que le modèle existe et est en stage "Production"
        model_versions = client.get_latest_versions(model_name, stages=[stage])
        if not model_versions:
            raise ValueError(f"Modèle '{model_name}' introuvable en stage '{stage}'")

        model_uri = f"models:/{model_name}/{stage}"
        logger.info(f"Chargement du modèle MLflow: {model_uri}")
        return mlflow.pyfunc.load_model(model_uri)
    except Exception as e:
        logger.error(f"Erreur de chargement du modèle {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Modèle non disponible: {e}")

def log_training_start(model_type: str) -> Dict[str, str]:
    """Démarre un run MLflow et log les paramètres initiaux."""
    mlflow.set_experiment(f"Rakuten_{model_type}_Training")
    run = mlflow.start_run()
    mlflow.log_param("model_type", model_type)
    mlflow.set_tag("status", "started")
    return {"run_id": run.info.run_id, "experiment_id": run.info.experiment_id}

def log_training_success(run_id: str, metrics: Dict[str, float]):
    """Log les métriques finales et marque le run comme réussi."""
    with mlflow.start_run(run_id=run_id):
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        mlflow.set_tag("status", "success")

# =========================
# ENDPOINTS
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/train/svm")
def train_svm(background_tasks: BackgroundTasks):
    """Démarre l'entraînement du modèle texte (SVM) en arrière-plan."""
    try:
        run_info = log_training_start("SVM")
        background_tasks.add_task(_train_svm_task, run_info["run_id"])
        return {
            "status": "svm_training_started",
            "run_id": run_info["run_id"],
            "experiment_id": run_info["experiment_id"]
        }
    except Exception as e:
        logger.error(f"Erreur de démarrage du training SVM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train/cnn")
def train_cnn(background_tasks: BackgroundTasks):
    """Démarre l'entraînement du modèle image (CNN) en arrière-plan."""
    try:
        run_info = log_training_start("CNN")
        background_tasks.add_task(_train_cnn_task, run_info["run_id"])
        return {
            "status": "cnn_training_started",
            "run_id": run_info["run_id"],
            "experiment_id": run_info["experiment_id"]
        }
    except Exception as e:
        logger.error(f"Erreur de démarrage du training CNN: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# TÂCHES D'ARRIÈRE-PLAN
# =========================
def _train_svm_task(run_id: str):
    """Tâche d'entraînement SVM avec gestion des erreurs."""
    try:
        from src.training.run_training_text import main_texte
        metrics = main_texte()
        log_training_success(run_id, {
            "accuracy": metrics["accuracy"],
            "f1_macro": metrics["f1_macro"]
        })
        logger.info("✅ Entraînement SVM terminé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'entraînement SVM: {e}")
        with mlflow.start_run(run_id=run_id):
            mlflow.set_tag("status", "failed")

def _train_cnn_task(run_id: str):
    """Tâche d'entraînement CNN avec gestion des erreurs."""
    try:
        from src.training.run_training_images import main_image
        metrics = main_image()
        log_training_success(run_id, {
            "accuracy": metrics["accuracy"],
            "f1_macro": metrics["f1_macro"]
        })
        logger.info("✅ Entraînement CNN terminé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'entraînement CNN: {e}")
        with mlflow.start_run(run_id=run_id):
            mlflow.set_tag("status", "failed")

# =========================
# CHARGEMENT DES MODÈLES (POUR INFERENCE)
# =========================
@app.on_event("startup")
async def startup_event():
    """Charge les modèles au démarrage pour l'inference."""
    try:
        global text_model, image_model
        text_model = load_mlflow_model("Text_Classifier_SVM")
        image_model = load_mlflow_model("Image_Classifier_CNN")
        logger.info("✅ Modèles chargés avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur de chargement des modèles: {e}")
        raise

    