"""
Preprocessing wrapper pour Airflow
  1. Exécute preprocessing.py → data/processed/ local
  2. dvc add + dvc push → DagsHub (versionnement des données processed)
  3. Écrit /tmp/data_version.txt pour la tâche train aval
"""

import os
import subprocess

from config.logging_config import get_logger
from src.preprocessing.preprocessing import preprocess

logger = get_logger(__name__)


def _dvc_push() -> None:
    """
    Versionne data/processed/ avec DVC et push vers DagsHub.
    Nécessite git + dvc[http] dans le container et les credentials
    DAGSHUB_USERNAME / DAGSHUB_USER_TOKEN en variables d'environnement.
    """
    dagshub_user  = os.getenv("DAGSHUB_USERNAME")
    dagshub_token = os.getenv("DAGSHUB_USER_TOKEN")

    if not dagshub_user or not dagshub_token:
        logger.warning("⚠️  DAGSHUB_USERNAME/TOKEN manquants — dvc push ignoré")
        return

    commands = [
        # Configure credentials DagsHub pour ce run
        ["dvc", "remote", "modify", "origin", "--local", "auth", "basic"],
        ["dvc", "remote", "modify", "origin", "--local", "user", dagshub_user],
        ["dvc", "remote", "modify", "origin", "--local", "password", dagshub_token],
        # Versionner et pusher data/processed/
        ["dvc", "add", "data/processed/"],
        ["dvc", "push"],
    ]

    for cmd in commands:
        logger.info(f"  $ {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"  ❌ {result.stderr}")
            raise RuntimeError(f"Commande échouée : {' '.join(cmd)}")
        if result.stdout:
            logger.info(f"  {result.stdout.strip()}")

    logger.info("✅ data/processed/ versionnée et pushée sur DagsHub")


def run_preprocessing():
    """Execute preprocessing and return version"""
    
    logger.info("🔄 Starting preprocessing pipeline...")
    
    try:
        data_version = preprocess(run_translation=True)
        logger.info(f"✅ Preprocessing completed : Data version: {data_version}")

        _dvc_push()
        
        # Write version to file for Airflow XCom
        with open("/tmp/data_version.txt", "w") as f:
            f.write(data_version)
        
        logger.info("✅ Data version saved for downstream tasks")
        
        return data_version
        
    except Exception as e:
        logger.error(f"❌ Preprocessing failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_preprocessing()