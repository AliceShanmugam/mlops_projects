# services/training/app/svm_adapter.py
from pathlib import Path
from src.models.train_linearsvm import train_and_evaluate_svm

def run_svm_training():
    metrics = train_and_evaluate_svm(
        data_path=Path("data/processed/train_clean.csv"),
        artifacts_dir=Path("models/run_linear_svm2"),
    )
    return metrics
