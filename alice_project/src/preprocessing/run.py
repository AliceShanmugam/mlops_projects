"""
Preprocessing wrapper for Airflow
Returns data_version for downstream tasks
"""

from config.logging_config import get_logger
from src.preprocessing.preprocessing import preprocess

logger = get_logger(__name__)

def run_preprocessing():
    """Execute preprocessing and return version"""
    
    logger.info("🔄 Starting preprocessing pipeline...")
    
    try:
        data_version = preprocess(run_translation=True)
        logger.info(f"✅ Preprocessing completed")
        logger.info(f"   Data version: {data_version}")
        
        # Write version to file for Airflow XCom
        with open("/tmp/data_version.txt", "w") as f:
            f.write(data_version)
        
        logger.info(f"✅ Data version saved for downstream tasks")
        
        return data_version
        
    except Exception as e:
        logger.error(f"❌ Preprocessing failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_preprocessing()