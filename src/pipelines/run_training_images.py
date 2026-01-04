
from pathlib import Path
import json

from src.preprocessing.text_cleaning import preprocess_training_data
from src.models.train_cnn import train_cnn

# =========================
# PATHS
# =========================
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models/images")

X_TRAIN_PATH = DATA_RAW_DIR / "X_train_update.csv"
Y_TRAIN_PATH = DATA_RAW_DIR / "Y_train_CVw08PX.csv"
TRAIN_CLEAN_PATH = DATA_PROCESSED_DIR / "train_clean.csv"


# =========================
# UTILS
# =========================
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

    # 1 Preprocess dataset (text + image_path + label)
    print("1 Preprocessing dataset (text + image paths)...")
    preprocess_training_data(
        x_path=X_TRAIN_PATH,
        y_path=Y_TRAIN_PATH,
        output_path=TRAIN_CLEAN_PATH,
        detect_lang=True,
    )

    # 2 Train CNN (images only)
    print("\n2 Training CNN from scratch...")
    metrics = train_cnn(
        data_path=TRAIN_CLEAN_PATH,
        artifacts_dir=MODELS_DIR,
    )

    # 3 Save metrics
    print("\n3 Save CNN metrics...")
    metrics_path = MODELS_DIR / "metrics_cnn.json"
    metrics = make_json_serializable(metrics)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n===============================")
    print(f" CNN model saved in: {MODELS_DIR.resolve()}")
    print(f" Metrics saved to: {metrics_path.resolve()}")
    print("===============================\n")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
