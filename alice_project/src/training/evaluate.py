"""
Model evaluation script
Compares new model with production model
"""

import os
import io
import joblib
from pathlib import Path
from sklearn.metrics import f1_score
import mlflow
import json

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

def evaluate(new_run_id: str, data_version: str):
    """Evaluate new model vs production model"""
    
    logger.info(f"📊 Starting model evaluation...")
    logger.info(f"   New run ID: {new_run_id}")
    logger.info(f"   Data version: {data_version}")
    
    # Setup MLFlow
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    
    logger.info("✅ Test data loaded")
    
    # Get new model from new run
    logger.info("🔍 Fetching new model from MLFlow...")
    client = mlflow.tracking.MlflowClient(settings.MLFLOW_TRACKING_URI)
    experiment = client.get_experiment_by_name("text_classification")
    exp_id = experiment.experiment_id if experiment else "0"
    new_run = client.get_run(new_run_id)
    new_f1 = new_run.data.metrics.get("f1_macro", 0)
    
    logger.info(f"   New model F1: {new_f1:.4f}")
    
    # Get current production model
    logger.info("🔍 Fetching production model metrics...")
    try:
        current_runs = client.search_runs(
            experiment_ids=[exp_id],  # Use the correct experiment ID
            filter_string="tags.model_stage = 'production'",
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if current_runs:
            prod_run = current_runs[0]
            prod_f1 = prod_run.data.metrics.get("f1_macro", 0)
            logger.info(f"   Production model F1: {prod_f1:.4f}")
        else:
            prod_f1 = 0
            logger.info("   No production model found (first training)")
        
        # Compare
        improvement = new_f1 - prod_f1
        logger.info(f"\n📈 Improvement: {improvement:+.4f} F1 points")
        
        if new_f1 > prod_f1:
            logger.info("✅ NEW MODEL IS BETTER - Ready for production")
            return {
                "should_promote": True,
                "new_f1": new_f1,
                "prod_f1": prod_f1,
                "improvement": improvement
            }
        else:
            logger.warning("⚠️ New model is NOT better - Keep current production")
            return {
                "should_promote": False,
                "new_f1": new_f1,
                "prod_f1": prod_f1,
                "improvement": improvement
            }
    
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python evaluate.py <new_run_id> <data_version>")
        sys.exit(1)
    
    evaluate(sys.argv[1], sys.argv[2])