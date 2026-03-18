from fastapi import FastAPI, BackgroundTasks
import mlflow
import logging
import dagshub

from src.training.run_training_text import main_texte
from src.training.run_training_images import main_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Training Service")
dagshub.init(repo_owner="Fouxy84", repo_name="mlops_projects", mlflow=True)


@app.get("/health")
def health():
    return {"status": "ok"}


def train_text_pipeline():
    with mlflow.start_run(run_name="Text_Training_SVM"):
        main_texte()
        mlflow.log_param("model_type", "SVM")
        logger.info("Modèle texte entraîné avec succès.")


def train_image_pipeline():
    with mlflow.start_run(run_name="Image_Training_CNN"):
        main_image()
        mlflow.log_param("model_type", "CNN")
        logger.info("Modèle image entraîné avec succès.")


@app.post("/train/svm")
def train_svm(background_tasks: BackgroundTasks):
    background_tasks.add_task(train_text_pipeline)
    return {"status": "svm_training_started"}


@app.post("/train/cnn")
def train_cnn(background_tasks: BackgroundTasks):
    background_tasks.add_task(train_image_pipeline)
    return {"status": "cnn_training_started"}
