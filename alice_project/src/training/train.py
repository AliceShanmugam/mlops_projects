"""
Training script for Airflow pipeline
Accepts data_version as argument from Airflow
"""

import os
import io
import joblib
import mlflow
import mlflow.sklearn
import boto3
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score, classification_report
from sklearn.pipeline import Pipeline
import argparse
from pathlib import Path

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

def _load_from_minio(s3, data_version: str, filename: str):
    buf = io.BytesIO(
        s3.get_object(Bucket='processed-data', Key=f'{data_version}/{filename}')['Body'].read()
    )
    return joblib.load(buf)

def train(data_version: str):
    """Train model with versioned data"""
    
    logger.info(f"🚀 Starting training with data version: {data_version}")
    
    # Setup MLFlow
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("text_classification")
    
    # Charger les données depuis MinIO
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio:9000'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )
    logger.info(f"📂 Loading data from MinIO: processed-data/{data_version}/")
    
    # Load data
    X_train = _load_from_minio(s3, data_version, "X_train_tfidf.joblib")
    y_train = _load_from_minio(s3, data_version, "y_train.joblib")
    X_test  = _load_from_minio(s3, data_version, "X_test_tfidf.joblib")
    y_test  = _load_from_minio(s3, data_version, "y_test.joblib")
    tfidf_vectorizer = _load_from_minio(s3, data_version, "tfidf_vectorizer.joblib")
    
    
    logger.info("✅ Data loaded successfully")
    logger.info(f"   X_train shape: {X_train.shape}")
    logger.info(f"   X_test shape: {X_test.shape}")
    
    # Start MLFlow run
    with mlflow.start_run():
        try:
            # Log parameters
            mlflow.log_param("model_type", "LinearSVC")
            mlflow.log_param("random_state", 42)
            mlflow.log_param("data_version", data_version)
            mlflow.log_param("max_iter", 2000)
            
            # Train model
            logger.info("⚙️ Training LinearSVC model...")
            model = LinearSVC(random_state=42, max_iter=2000, verbose=1)
            model.fit(X_train, y_train)
            logger.info("✅ Model trained successfully")
            
            # Predictions
            logger.info("📊 Making predictions on test set...")
            y_pred = model.predict(X_test)
            
            # Evaluation
            f1_macro = f1_score(y_test, y_pred, average="macro")
            logger.info(f"📈 F1-score (macro): {f1_macro:.4f}")
            
            # Log report
            report = classification_report(y_test, y_pred)
            logger.info(f"\n{report}")
            
            # Log metrics
            mlflow.log_metric("f1_macro", f1_macro)
            
            # Save and log artifacts
            models_path = Path(settings.MODELS_PATH)
            models_path.mkdir(exist_ok=True, parents=True)
            
            logger.info("💾 Saving model artifacts...")
            joblib.dump(model, models_path / "svm.joblib")
            joblib.dump(tfidf_vectorizer, models_path / "tfidf_vectorizer.joblib")
            
            # Create and save pipeline
            pipeline = Pipeline([
                ("tfidf", tfidf_vectorizer),
                ("svm", model)
            ])
            joblib.dump(pipeline, models_path / "text_pipeline.joblib")
            
            # Log to MLFlow
            mlflow.sklearn.log_model(pipeline, "model")
            mlflow.log_artifact(str(models_path / "svm.joblib"))
            
            # Save classification report
            report_path = Path("/tmp/classification_report.txt")
            with open(report_path, "w") as f:
                f.write(report)
            mlflow.log_artifact(str(report_path))
            
            logger.info("✅ Model artifacts saved and logged to MLFlow")
            logger.info(f"🎉 Training completed successfully!")

            run_id = mlflow.active_run().info.run_id

            # Sauvegarder le run_id pour la task suivante (evaluate)
            with open('/tmp/mlflow_run_id.txt', 'w') as f:
                f.write(run_id)
            
            return {
                "status": "success",
                "f1_score": float(f1_macro),
                "model_path": str(models_path / "svm.joblib"),
                "run_id": mlflow.active_run().info.run_id
            }
            
        except Exception as e:
            logger.error(f"❌ Training failed: {str(e)}", exc_info=True)
            mlflow.log_param("error", str(e))
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_version", required=True, help="Data version directory name")
    args = parser.parse_args()
    
    train(args.data_version)