
from src.pipelines.run_training_text import main
from src.pipelines.run_training_images import main
import mlflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Entraînement SVM (texte)
    with mlflow.start_run(run_name="Text_Training_SVM"):
        train_text_pipeline(
            data_path="/app/data/raw/X_train.csv",
            target_path="/app/data/raw/Y_train.csv",
            output_dir="/app/models/text"
        )
        mlflow.log_param("model_type", "SVM")
        logger.info("Modèle texte entraîné avec succès.")

    # Entraînement CNN (images)
    with mlflow.start_run(run_name="Image_Training_CNN"):
        train_images_pipeline(
            data_path="/app/data/raw/image_train",
            output_dir="/app/models/images"
        )
        mlflow.log_param("model_type", "CNN")
        logger.info("Modèle image entraîné avec succès.")
