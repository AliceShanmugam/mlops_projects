
# src/run_training_text.py

from pathlib import Path
import json

from src.preprocessing.text_cleaning import preprocess_training_data
from src.features.build_features import train_tfidf_vectorizer
from src.models.train_linearsvm import train_and_evaluate_svm


# =========================
# PATHS
# =========================
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models/text")

X_TRAIN_PATH = DATA_RAW_DIR / "X_train_update.csv"
Y_TRAIN_PATH = DATA_RAW_DIR / "Y_train_CVw08PX.csv"
TRAIN_CLEAN_PATH = DATA_PROCESSED_DIR / "train_clean.csv"

def make_json_serializable(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    return obj

# =========================
# PIPELINE
# =========================
def main():

    # 1 Preprocess raw data
    print("1 Preprocessing text dataset...")
    preprocess_training_data(
        x_path=X_TRAIN_PATH,
        y_path=Y_TRAIN_PATH,
        output_path=TRAIN_CLEAN_PATH,
    )

    # 2 Train TF-IDF
    print("\n2 Training TF-IDF vectorizer...")
    train_tfidf_vectorizer(
        data_path=TRAIN_CLEAN_PATH,
        artifacts_dir=MODELS_DIR,
        text_column="text_clean",
        max_features=20000,
        ngram_range=(1, 2),
        add_images=True,
    )

    # 3 Train Linear SVM
    print("\n3 Training Linear SVM...")
    metrics = train_and_evaluate_svm(
        data_path=TRAIN_CLEAN_PATH,
        artifacts_dir=MODELS_DIR,
        test_size=0.2,
        svm_params={"C": 1.0},
    )
    
    # 4 Save metrics
    print("\n4 Save model's metrics...")
    metrics_path = MODELS_DIR / "metrics_text.json"
    metrics = make_json_serializable(metrics)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    
    print("\n===============================")
    print(f"Models saved in: {MODELS_DIR.resolve()}")
    print(f"Metrics saved to: {metrics_path.resolve()}\n")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
