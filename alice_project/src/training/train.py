"""
Training script for Airflow pipeline.
Lit les données preprocessées depuis DATA_PROCESSED_PATH (data/processed/ local),
entraîne un LinearSVC et log les résultats sur DagsHub via MLFlow.
"""

import argparse
import json
import os
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

def _load(filename: str, data_dir: str) -> object:
    path = os.path.join(data_dir, filename)
    logger.info(f"  📂 Chargement : {path}")
    return joblib.load(path)

def _read_lineage(data_dir: str) -> dict:
    """Lit data/processed/lineage.json pour enrichir les tags MLFlow (data lineage)."""
    lineage_path = os.path.join(data_dir, "lineage.json")
    if os.path.exists(lineage_path):
        with open(lineage_path) as f:
            return json.load(f)
    return {}


def train(data_version: str):
    """
    Entraîne le modèle texte (LinearSVC + TF-IDF) sur les données preprocessées.

    Args:
        data_version: Timestamp YYYYMMDD_HHMMSS issu du preprocessing.
                      Loggé dans MLFlow pour la traçabilité.
    """
    data_dir = os.getenv("DATA_PROCESSED_DIR", "/app/data/processed")
    logger.info(f"🚀 Starting training with data version: {data_version}")
    logger.info(f"   Données depuis : {data_dir}")
    
    # Setup MLFlow → DagsHub
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("text_classification")
    
    # Chargement des données preprocessées locales
    X_train          = _load("X_train_tfidf.joblib", data_dir)
    y_train          = _load("y_train.joblib", data_dir)
    X_test           = _load("X_test_tfidf.joblib", data_dir)
    y_test           = _load("y_test.joblib", data_dir)
    tfidf_vectorizer = _load("tfidf_vectorizer.joblib", data_dir)
    
    
    logger.info(f"✅ Données chargées — X_train: {X_train.shape}, X_test: {X_test.shape}")

    # Data lineage depuis lineage.json
    lineage = _read_lineage(data_dir=data_dir)
    
    # Start MLFlow run
    with mlflow.start_run():
        try:
            # Log parameters
            mlflow.log_param("model_type", "LinearSVC")
            mlflow.log_param("random_state", 42)
            mlflow.log_param("max_iter", 2000)
            mlflow.log_param("data_version", data_version)
            
            # Data lineage tags — relie ce run aux données sources
            mlflow.set_tag("data_version",   data_version)
            mlflow.set_tag("download_date",  lineage.get("download_date", "unknown"))
            mlflow.set_tag("processed_at",   lineage.get("processed_at", "unknown"))
            mlflow.set_tag("data_n_rows",    str(lineage.get("n_rows", "unknown")))
            mlflow.set_tag("data_raw_path",  lineage.get("source_raw_path", "unknown"))

            # Train model
            logger.info("⚙️ Training LinearSVC model...")
            model = LinearSVC(random_state=42, max_iter=2000, verbose=1)
            model.fit(X_train, y_train)
            logger.info("✅ Model trained successfully")
            
            # Evaluation
            y_pred = model.predict(X_test)
            f1_macro = f1_score(y_test, y_pred, average="macro")
            report   = classification_report(y_test, y_pred)
            
            logger.info(f"📈 F1-score (macro): {f1_macro:.4f}")
            logger.info(f"\n{report}")
            
            mlflow.log_metric("f1_macro", f1_macro)
            
            # Save and log artifacts
            models_path = Path(settings.MODELS_PATH)
            models_path.mkdir(exist_ok=True, parents=True)
            
            joblib.dump(model, models_path / "svm.joblib")
            joblib.dump(tfidf_vectorizer, models_path / "tfidf_vectorizer.joblib")
            
            # Create and save pipeline
            pipeline = Pipeline([
                ("tfidf", tfidf_vectorizer),
                ("svm", model)
            ])
            joblib.dump(pipeline, models_path / "text_pipeline.joblib")
            
            logger.info(f"💾 Modèles sauvegardés dans {models_path}")
            
            # Log to MLFlow
            mlflow.sklearn.log_model(pipeline, "model")
            mlflow.log_artifact(str(models_path / "svm.joblib"))
            
            # Save classification report
            report_path = Path("/tmp/classification_report.txt")
            report_path.write_text(report)
            mlflow.log_artifact(str(report_path))
            
            logger.info("✅ Model artifacts saved and logged to MLFlow")
   

            run_id = mlflow.active_run().info.run_id

            # Sauvegarder le run_id pour la task suivante (evaluate)
            with open('/tmp/mlflow_run_id.txt', 'w') as f:
                f.write(run_id)
            
            logger.info(f"🎉 Entraînement terminé — run_id: {run_id}")

            return {
                "status": "success",
                "f1_score": float(f1_macro),
                "run_id": run_id,
                "model_path": str(models_path / "svm.joblib"),
            }
            
        except Exception as e:
            logger.error(f"❌ Training failed: {str(e)}", exc_info=True)
            mlflow.log_param("error", str(e))
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_version", required=True, help="Timestamp YYYYMMDD_HHMMSS issu du preprocessing")
    args = parser.parse_args()
    
    train(args.data_version)