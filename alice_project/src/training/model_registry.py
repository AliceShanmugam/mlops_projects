"""
Model registry management
Tags models as production in MLFlow
"""

import mlflow
from datetime import datetime

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

def promote_model_to_production(new_run_id: str, previous_run_id: str = None):
    """
    Promote new model to production and demote previous
    """
    
    logger.info(f"📦 Promoting model {new_run_id} to production...")
    
    # Setup MLFlow
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient(settings.MLFLOW_TRACKING_URI)
    
    try:
        # Get all registered models
        registered_models = client.search_registered_models()
        logger.info(f"   Found {len(registered_models)} registered models")
        
        # Remove 'production' tag from previous models
        if previous_run_id:
            logger.info("   Removing 'production' tag from previous run...")
            old_run = client.get_run(previous_run_id)
            client.set_tag(previous_run_id, "model_stage", "archived")
            logger.info("   ✅ Previous model archived")
        
        # Tag new model as production
        logger.info("   Tagging new run as production...")
        client.set_tag(new_run_id, "model_stage", "production")
        client.set_tag(new_run_id, "promoted_at", datetime.now().isoformat())
        
        logger.info("✅ Model promoted to production successfully!")
        
        return {
            "status": "success",
            "run_id": new_run_id,
            "promoted_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Model promotion failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    import os, sys, requests
    import mlflow
    from config.settings import settings

    new_run_id = sys.argv[1]
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient(settings.MLFLOW_TRACKING_URI)

    new_run = client.get_run(new_run_id)
    new_f1   = new_run.data.metrics.get('f1_macro', 0)
    exp_id   = new_run.info.experiment_id

    current_runs = client.search_runs(
        experiment_ids=[exp_id],
        filter_string="tags.model_stage = 'production'",
        order_by=["start_time DESC"],
        max_results=1,
    )
    prod_f1 = current_runs[0].data.metrics.get('f1_macro', 0) if current_runs else 0

    print(f"📊 Nouveau: F1={new_f1:.4f} | Production: F1={prod_f1:.4f}")

    if new_f1 > prod_f1:
        if current_runs:
            client.set_tag(current_runs[0].info.run_id, 'model_stage', 'archived')
        client.set_tag(new_run_id, 'model_stage', 'production')
        client.set_tag(new_run_id, 'promoted_at', datetime.now().isoformat())
        try:
            resp = requests.post(
                f"{os.getenv('API_SERVICE_URL', 'http://api:8000')}/models/reload",
                headers={"X-API-Key": os.getenv("ADMIN_API_KEY")},
                timeout=10,
            )
            print(f"✅ API reload: {resp.status_code}")
        except Exception as e:
            print(f"⚠️ API reload échoué: {e}")
        print("✅ Nouveau modèle promu en production")
    else:
        client.set_tag(new_run_id, 'model_stage', 'rejected')
        print("⚠️ Modèle non promu — pas d'amélioration")