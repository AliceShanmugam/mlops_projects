
from src.training.run_training_text import main_texte
from src.training.run_training_images import main_image
import mlflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Entraînement SVM (texte)
    with mlflow.start_run(run_name="Text_Training_SVM"):
        main_texte()
            #data_path="/app/data/raw/X_train.csv",
            #target_path="/app/data/raw/Y_train.csv",
            #output_dir="/app/src/mlflow/mlruns"
        #)
        mlflow.log_param("model_type", "SVM")
        logger.info("Modèle texte entraîné avec succès.")

    # Entraînement CNN (images)
    with mlflow.start_run(run_name="Image_Training_CNN"):
        main_image()
            #data_path="/app/data/raw/image_train",
            #output_dir="/app/src/mlflow/mlruns"
        #)
        mlflow.log_param("model_type", "CNN")
        logger.info("Modèle image entraîné avec succès.")
