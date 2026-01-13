
# src/run_training_text.py

from pathlib import Path
import json
import mlflow
from src.preprocessing.text_cleaning import preprocess_training_data
from src.preprocessing.train_tfidf import train_tfidf_vectorizer
from src.train_models.train_linearsvm import train_and_evaluate_svm


# =========================
# PATHS
# =========================
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("src/mlflow/mlruns")

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
def main_texte():
    mlflow.set_experiment("Texte_Pipeline")
    with mlflow.start_run(run_name="Full_Texte_Pipeline"):
        mlflow.set_tag("step", "preprocessing")
        print("\n")
        print("1. Preprocessing dataset (text + image)")
        preprocess_training_data(
            x_path=X_TRAIN_PATH,
            y_path=Y_TRAIN_PATH,
            output_path=TRAIN_CLEAN_PATH,
            detect_lang=True,
        )
        mlflow.log_artifact(TRAIN_CLEAN_PATH, "preprocessed_data")
        print(f"Dataset préprocessé sauvegardé: {TRAIN_CLEAN_PATH}")
        
        mlflow.set_tag("step", "vectorization")
        print("\n")
        print("2. Training TF-IDF vectorizer")
        train_tfidf_vectorizer(
            data_path=TRAIN_CLEAN_PATH,
            artifacts_dir=MODELS_DIR,
            text_column="text_clean",
            max_features=50000,
            ngram_range=(1, 2)
        )

        mlflow.set_tag("step", "training")
        print("\n")
        print("3. Training Linear SVM")
        metrics = train_and_evaluate_svm(
            data_path=TRAIN_CLEAN_PATH,
            artifacts_dir=MODELS_DIR,
            test_size=0.2,
            svm_params={"C": 1.0}
        )
        
        mlflow.set_tag("step", "metrics")
        print("\n")
        print("3. Save global metrics")
        metrics_path = MODELS_DIR / "metrics_svm_pipeline.json"
        metrics = make_json_serializable(metrics)
        mlflow.log_metric("texte_pipeline_accuracy",metrics["accuracy"])
        mlflow.log_metric("texte_pipeline_f1",metrics["f1_macro"])

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as f:
               json.dump(metrics, f, indent=2)
        mlflow.log_artifact(metrics_path, "texte_pipeline_metrics")

        mlflow.set_tag("status", "success")
        mlflow.set_tag("pipeline", "texte_classification")
        
        print("\n===============================")
        print(" Pipeline texte terminé avec succès!")
        print(f"   - Modèle SVM: {MODELS_DIR.resolve()}/cnn.pt")
        print(f"   - Métriques_SVM: {metrics_path.resolve()}")
        print(f"   - Run MLflow: {metrics['mlflow_run_id']}")
        print("===============================\n")
       
        
# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main_texte()
