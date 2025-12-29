from pathlib import Path
from src.models.train_svm import train_and_evaluate_svm

def test_train_svm_pipeline(tmp_path):
    metrics = train_and_evaluate_svm(
        data_path=Path("data/processed/train_clean.csv"),
        artifacts_dir=tmp_path,
    )
    assert "f1_macro" in metrics
