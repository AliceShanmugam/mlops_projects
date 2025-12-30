import pandas as pd
from pathlib import Path

from src.models.train_linearsvm import train_and_evaluate_svm


def test_training_pipeline_creates_artifacts(tmp_path):
    # --- Fake dataset (3 classes) ---
    df = pd.DataFrame({
        "text_clean": [
            "console de jeu",
            "jeu video pc",
            "livre de cuisine",
            "roman policier",
            "chaise de bureau",
            "table en bois"
        ],
        "label": [0, 0, 1, 1, 2, 2]
    })

    data_path = tmp_path / "train_clean.csv"
    df.to_csv(data_path, index=False)

    artifacts_dir = tmp_path / "artifacts"

    # --- Force safe split for CI ---
    metrics = train_and_evaluate_svm(
        data_path=data_path,
        artifacts_dir=artifacts_dir,
        tfidf_params={"max_features": 50, "ngram_range": (1, 1)},
        svm_params={"C": 1.0},
        test_size=0.5   # 🔑 clé de la robustesse
    )

    assert (artifacts_dir / "tfidf.joblib").exists()
    assert (artifacts_dir / "svm.joblib").exists()
    assert isinstance(metrics["f1_macro"], float)
