# src/models/train_linearsvm.py

from pathlib import Path
import joblib
import pandas as pd
import json
import mlflow

from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, accuracy_score


# =========================
# LOAD DATA
# =========================
def load_processed_data(csv_path: Path):
    df = pd.read_csv(csv_path)

    required_cols = {"text_clean", "label"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing columns: {required_cols - set(df.columns)}")

    X = df["text_clean"].astype(str)
    y = df["label"].astype(int)

    return X, y


# =========================
# TRAIN LINEAR SVM
# =========================
def train_and_evaluate_svm(
    data_path: Path,
    artifacts_dir: Path,
    test_size: float = 0.2,
    svm_params: dict | None = None,
    experiment_name : str = "text_classification_svm",
    run_name : str = "run_svm_1"
):

    svm_params = svm_params or {}
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    tfidf_path = artifacts_dir / "tfidf.joblib"
    if not tfidf_path.exists():
        raise FileNotFoundError("tfidf.joblib not found. Train TF-IDF first.")

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name, nested=True):
        
        X_text, y = load_processed_data(data_path)
        stratify = y if len(set(y)) > 1 else None
        X_train, X_val, y_train, y_val = train_test_split(X_text,y,test_size=test_size,random_state=42,stratify=stratify)
        vectorizer = joblib.load(tfidf_path)
        X_train_vec = vectorizer.transform(X_train)
        X_val_vec = vectorizer.transform(X_val)
        svm = LinearSVC(C=svm_params.get("C", 1.0),max_iter=5000)
        svm.fit(X_train_vec, y_train)
        svm_path = artifacts_dir / "svm.joblib"
        joblib.dump(svm, svm_path)
        # mlflow save svm model
        mlflow.log_artifact(svm_path,"svm_model")

        y_pred = svm.predict(X_val_vec)
        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average="macro")
        report = classification_report(y_val,y_pred,output_dict=True,zero_division=0)   
        report_path = artifacts_dir / "report_text.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        mlflow.log_artifact(report_path,"metrics_json")   
        
        #mlflow log parameters
        mlflow.log_param("model_type", "LinearSVM")
        mlflow.log_param("C", svm.C)
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("n_train", len(X_train))
        mlflow.log_param("n_val", len(X_val))
        mlflow.log_param("tfidf_features", X_train_vec.shape[1])
        #mlflow log metrics
        mlflow.log_metric("f1_macro", f1)
        mlflow.log_metric("accuracy", accuracy)

        print(f"SVM saved to {svm_path}")
        print(f"F1 macro: {f1:0.4f}")
        print(f"accuracy: {accuracy:0.4f}")
        print("mlflow_run_id ",mlflow.active_run().info.run_id)

        return {"svm_model": svm,"f1_macro": f1,"classification_report": report,"svm_path": svm_path,"accuracy":accuracy,"mlflow_run_id": mlflow.active_run().info.run_id}



