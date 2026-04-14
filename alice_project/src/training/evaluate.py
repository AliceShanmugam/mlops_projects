"""
Model evaluation script
Compares new model with production model via MLFlow (DagsHub)
"""

import sys
import mlflow

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

def evaluate(new_run_id: str, data_version: str):
    """
    Compare le nouveau modèle avec le modèle en production dans MLFlow.

    Args:
        new_run_id:    run_id MLFlow du nouveau modèle (écrit par train.py)
        data_version:  timestamp YYYYMMDD_HHMMSS du preprocessing (pour logs)

    Returns:
        dict avec should_promote, new_f1, prod_f1, improvement
    """
    
    logger.info("📊 Starting model evaluation...")
    logger.info(f"   New run ID: {new_run_id}")
    logger.info(f"   Data version: {data_version}")
    
    # Setup MLFlow
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient(settings.MLFLOW_TRACKING_URI)

    # Métriques du nouveau modèle
    new_run = client.get_run(new_run_id)
    new_f1  = new_run.data.metrics.get("f1_macro", 0)
    exp_id  = new_run.info.experiment_id
    logger.info(f"   New model F1:  {new_f1:.4f}")

    # Métriques du modèle actuellement en production
    current_runs = client.search_runs(
        experiment_ids=[exp_id],
        filter_string="tags.model_stage = 'production'",
        order_by=["start_time DESC"],
        max_results=1,
    )

    if current_runs:
        prod_f1 = current_runs[0].data.metrics.get("f1_macro", 0)
        logger.info(f"   Production F1: {prod_f1:.4f}")
    else:
        prod_f1 = 0
        logger.info("   No production model found (first training)")

    improvement = new_f1 - prod_f1
    logger.info(f"\n📈 Improvement: {improvement:+.4f} F1 points")

    if new_f1 > prod_f1:
        logger.info("✅ NEW MODEL IS BETTER — Ready for production")
    else:
        logger.warning("⚠️  New model is NOT better — Keep current production")

    # Écrit le résultat pour la tâche registry_task (PythonOperator Airflow)
    result = {
        "should_promote": new_f1 > prod_f1,
        "new_f1":         new_f1,
        "prod_f1":        prod_f1,
        "improvement":    improvement,
        "new_run_id":     new_run_id,
    }

    with open("/tmp/evaluation_result.json", "w") as f:
        import json
        json.dump(result, f)

    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python evaluate.py <new_run_id> <data_version>")
        sys.exit(1)
    evaluate(sys.argv[1], sys.argv[2])