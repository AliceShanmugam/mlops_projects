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
            logger.info(f"   Removing 'production' tag from previous run...")
            old_run = client.get_run(previous_run_id)
            client.set_tag(previous_run_id, "model_stage", "archived")
            logger.info("   ✅ Previous model archived")
        
        # Tag new model as production
        logger.info(f"   Tagging new run as production...")
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
    import sys
    new_run_id = sys.argv[1] if len(sys.argv) > 1 else None
    prev_run_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not new_run_id:
        print("Usage: python model_registry.py <new_run_id> [previous_run_id]")
        sys.exit(1)
    
    promote_model_to_production(new_run_id, prev_run_id)