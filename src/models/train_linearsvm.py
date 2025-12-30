
from pathlib import Path
import joblib
import pandas as pd

from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer


def load_processed_data(csv_path: Path):
    df = pd.read_csv(csv_path)
    X = df["text_clean"].astype(str)
    y = df["label"].astype(int)
    return X, y


def train_and_evaluate_svm(
    data_path: Path,
    artifacts_dir: Path,
    tfidf_params: dict | None = None,
    svm_params: dict | None = None,
    test_size: float = 0.2,   # 🔑 paramètre contrôlable
):
    tfidf_params = tfidf_params or {}
    svm_params = svm_params or {}

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # --- Load data ---
    X_text, y = load_processed_data(data_path)

    # --- Split (robuste CI & prod) ---
    stratify = y if len(set(y)) < len(y) else None

    X_train_text, X_val_text, y_train, y_val = train_test_split(
        X_text,
        y,
        test_size=test_size,
        random_state=42,
        stratify=stratify
    )

    # --- TF-IDF ---
    vectorizer = TfidfVectorizer(
        max_features=tfidf_params.get("max_features", 20000),
        ngram_range=tfidf_params.get("ngram_range", (1, 2)),
        sublinear_tf=True,
    )

    X_train_vec = vectorizer.fit_transform(X_train_text)
    joblib.dump(vectorizer, artifacts_dir / "tfidf.joblib")

    # --- Linear SVM ---
    svm = LinearSVC(
        C=svm_params.get("C", 1.0),
        max_iter=5000
    )
    svm.fit(X_train_vec, y_train)
    joblib.dump(svm, artifacts_dir / "svm.joblib")

    # --- Evaluation ---
    X_val_vec = vectorizer.transform(X_val_text)
    y_pred = svm.predict(X_val_vec)

    f1 = f1_score(y_val, y_pred, average="macro")
    #report = classification_report(y_val, y_pred, output_dict=True)
    report = classification_report(
    y_val,
    y_pred,
    output_dict=True,
    zero_division=0)


    return {
        "f1_macro": f1,
        "classification_report": report,
        "tfidf_path": artifacts_dir / "tfidf.joblib",
        "svm_path": artifacts_dir / "svm.joblib",
    }
