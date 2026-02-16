
# # src/training/run_training_text.py

# from pathlib import Path
# import json
# import mlflow
# from src.preprocessing.text_cleaning import preprocess_training_data
# from src.preprocessing.train_tfidf import train_tfidf_vectorizer
# from src.train_models.train_linearsvm import train_and_evaluate_svm


# # =========================
# # PATHS
# # =========================
# DATA_RAW_DIR = Path("data/raw")
# DATA_PROCESSED_DIR = Path("data/processed")
# MODELS_DIR = Path("src/mlflow/mlruns")

# X_TRAIN_PATH = DATA_RAW_DIR / "X_train_update.csv"
# Y_TRAIN_PATH = DATA_RAW_DIR / "Y_train_CVw08PX.csv"
# TRAIN_CLEAN_PATH = DATA_PROCESSED_DIR / "train_clean.csv"

# def make_json_serializable(obj):
#     if isinstance(obj, Path):
#         return str(obj)
#     if isinstance(obj, dict):
#         return {k: make_json_serializable(v) for k, v in obj.items()}
#     if isinstance(obj, list):
#         return [make_json_serializable(v) for v in obj]
#     return obj

# # =========================
# # PIPELINE
# # =========================
# def main_texte():
#     mlflow.set_experiment("Texte_Pipeline")
#     with mlflow.start_run(run_name="Full_Texte_Pipeline",nested=True):
#         mlflow.set_tag("step", "preprocessing")
#         print("\n")
#         print("1. Preprocessing dataset (text + image)")
#         preprocess_training_data(
#             x_path=X_TRAIN_PATH,
#             y_path=Y_TRAIN_PATH,
#             output_path=TRAIN_CLEAN_PATH,
#             detect_lang=True,
#         )
#         mlflow.log_artifact(TRAIN_CLEAN_PATH, "preprocessed_data")
#         print(f"Dataset préprocessé sauvegardé: {TRAIN_CLEAN_PATH}")
        
#         mlflow.set_tag("step", "vectorization")
#         print("\n")
#         print("2. Training TF-IDF vectorizer")
#         train_tfidf_vectorizer(
#             data_path=TRAIN_CLEAN_PATH,
#             artifacts_dir=MODELS_DIR,
#             text_column="text_clean",
#             max_features=50000,
#             ngram_range=(1, 2)
#         )

#         mlflow.set_tag("step", "training")
#         print("\n")
#         print("3. Training Linear SVM")
#         metrics = train_and_evaluate_svm(
#             data_path=TRAIN_CLEAN_PATH,
#             artifacts_dir=MODELS_DIR,
#             test_size=0.2,
#             svm_params={"C": 1.0}
#         )
        
#         mlflow.set_tag("step", "metrics")
#         print("\n")
#         print("3. Save global metrics")
#         metrics_path = MODELS_DIR / "metrics_svm_pipeline.json"
#         metrics = make_json_serializable(metrics)
#         mlflow.log_metric("texte_pipeline_accuracy",metrics["accuracy"])
#         mlflow.log_metric("texte_pipeline_f1",metrics["f1_macro"])

#         MODELS_DIR.mkdir(parents=True, exist_ok=True)
#         with open(metrics_path, "w", encoding="utf-8") as f:
#                json.dump(metrics, f, indent=2)
#         mlflow.log_artifact(metrics_path, "texte_pipeline_metrics")

#         mlflow.set_tag("status", "success")
#         mlflow.set_tag("pipeline", "texte_classification")
        
#         print("\n===============================")
#         print(" Pipeline texte terminé avec succès!")
#         print(f"   - Modèle SVM: {MODELS_DIR.resolve()}/cnn.pt")
#         print(f"   - Métriques_SVM: {metrics_path.resolve()}")
#         print(f"   - Run MLflow: {metrics['mlflow_run_id']}")
#         print("===============================\n")
       
        
# # =========================
# # ENTRY POINT
# # =========================
# if __name__ == "__main__":
#     main_texte()
    
from pathlib import Path
import json
import mlflow
from mlflow.tracking import MlflowClient
from src.preprocessing.text_cleaning import preprocess_training_data
from src.preprocessing.train_tfidf import train_tfidf_vectorizer
from src.train_models.train_linearsvm import train_and_evaluate_svm
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# PATHS (CORRIGÉS)
# =========================
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models/text")  # Chemin corrigé

X_TRAIN_PATH = DATA_RAW_DIR / "X_train_update.csv"
Y_TRAIN_PATH = DATA_RAW_DIR / "Y_train_CVw08PX.csv"
TRAIN_CLEAN_PATH = DATA_PROCESSED_DIR / "train_clean.csv"

# =========================
# UTILITAIRES
# =========================
def make_json_serializable(obj):
    """Rend un objet JSON-sérialisable."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    return obj

# =========================
# PIPELINE COMPLET
# =========================
def main_texte():
    """Pipeline complet pour l'entraînement du modèle texte."""
    uri = "file:///C:/Users/coach/Desktop/datascientest/Projet DATASCIENTEST/projet_MLops/mlops_projects/src/mlflow/mlflow.db"
    mlflow.set_tracking_uri(uri)  # Assure-toi que le serveur MLflow est en cours d'exécution
    mlflow.set_experiment("Rakuten_Text_Pipeline")

    with mlflow.start_run(run_name="Full_Text_Pipeline"):
        try:
            # 1. Préprocessing
            mlflow.set_tag("step", "preprocessing")
            logger.info("1. Préprocessing du dataset...")
            preprocess_training_data(
                x_path=X_TRAIN_PATH,
                y_path=Y_TRAIN_PATH,
                output_path=TRAIN_CLEAN_PATH,
                detect_lang=True,
            )
            mlflow.log_artifact(TRAIN_CLEAN_PATH, "preprocessed_data")
            logger.info(f"✅ Dataset préprocessé: {TRAIN_CLEAN_PATH}")

            # 2. Vectorisation TF-IDF
            mlflow.set_tag("step", "vectorization")
            logger.info("2. Entraînement du vectorizer TF-IDF...")
            X_vec, vectorizer = train_tfidf_vectorizer(
                data_path=TRAIN_CLEAN_PATH,
                artifacts_dir=MODELS_DIR,
                text_column="text_clean",
                max_features=50000,
                ngram_range=(1, 2)
            )
            mlflow.log_artifact(MODELS_DIR / "tfidf.joblib", "preprocessing")
            logger.info("✅ Vectorizer TF-IDF entraîné et sauvegardé")

            # 3. Entraînement SVM
            mlflow.set_tag("step", "training")
            logger.info("3. Entraînement du modèle SVM...")
            metrics = train_and_evaluate_svm(
                data_path=TRAIN_CLEAN_PATH,
                artifacts_dir=MODELS_DIR,
                test_size=0.2,
                svm_params={"C": 1.0}
            )

            # 4. Enregistrement du modèle dans le registry MLflow
            mlflow.sklearn.log_model(
                sk_model=metrics["svm_model"],  # Assure-toi que train_linearsvm.py retourne le modèle
                artifact_path="model",
                registered_model_name="Text_Classifier_SVM"
            )

            # Transition vers le stage "Production"
            client = MlflowClient()
            client.transition_model_version_stage(
                name="Text_Classifier_SVM",
                version=mlflow.active_run().info.run_id,
                stage="Production"
            )

            # 5. Sauvegarde des métriques
            mlflow.set_tag("step", "metrics")
            logger.info("4. Sauvegarde des métriques...")
            metrics_path = MODELS_DIR / "metrics_svm.json"
            metrics_serializable = make_json_serializable(metrics)
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics_serializable, f, indent=2)
            mlflow.log_artifact(metrics_path, "metrics")
            mlflow.log_metrics({
                "accuracy": metrics["accuracy"],
                "f1_macro": metrics["f1_macro"]
            })

            # Tags finaux
            mlflow.set_tag("status", "success")
            mlflow.set_tag("pipeline", "text_classification")

            logger.info("\n===============================")
            logger.info("🎯 Pipeline texte terminé avec succès!")
            logger.info(f"   - Modèle SVM: {MODELS_DIR.resolve()}/svm.joblib")
            logger.info(f"   - Métriques: {metrics_path.resolve()}")
            logger.info(f"   - Run MLflow: {mlflow.active_run().info.run_id}")
            logger.info("===============================\n")

            return metrics_serializable

        except Exception as e:
            logger.error(f"❌ Erreur dans le pipeline texte: {e}", exc_info=True)
            mlflow.set_tag("status", "failed")
            raise

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main_texte()
