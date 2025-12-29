
from pathlib import Path
import joblib
import pandas as pd

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from sklearn.feature_extraction.text import TfidfVectorizer


# =========================
# Load processed data
# =========================
def load_processed_data(csv_path: Path):
    """
    Load preprocessed training data.
    """
    df = pd.read_csv(csv_path)

    if "text_clean" not in df.columns or "label" not in df.columns:
        raise ValueError("Dataset must contain 'text_clean' and 'label' columns")

    X_text = df["text_clean"].astype(str)
    y = df["label"].astype(int)

    return X_text, y


# =========================
# Train SVM
# =========================
def train_svm(
    X_features,
    y,
    C: float = 1.0,
):
    """
    Train a linear SVM classifier with probabilities.
    """
    model = SVC(
        kernel="linear",
        probability=True,
        random_state=42,
        C=C
    )
    model.fit(X_features, y)
    return model


# =========================
# Train + Evaluate
# =========================
def train_and_evaluate_svm(
    data_path: Path,
    artifacts_dir: Path,
    tfidf_params: dict | None = None,
    svm_params: dict | None = None,
):
    """
    End-to-end training pipeline:
    - split train/validation
    - fit TF-IDF on train only
    - train SVM
    - evaluate with classification report
    - save TF-IDF and SVM artifacts
    """

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    tfidf_params = tfidf_params or {}
    svm_params = svm_params or {}

    # Load data
    X_text, y = load_processed_data(data_path)

    # Train / validation split
    X_train_text, X_val_text, y_train, y_val = train_test_split(
        X_text,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # =========================
    # TF-IDF (fit ONLY on train)
    # =========================
    vectorizer = TfidfVectorizer(
        max_features=tfidf_params.get("max_features", 50000),
        ngram_range=tfidf_params.get("ngram_range", (1, 2)),
        sublinear_tf=True,
    )

    X_train_vec = vectorizer.fit_transform(X_train_text)

    # Save TF-IDF
    joblib.dump(vectorizer, artifacts_dir / "tfidf.joblib")

    # =========================
    # Train SVM
    # =========================
    svm = train_svm(X_train_vec, y_train, **svm_params)

    # =========================
    # Evaluation
    # =========================
    X_val_vec = vectorizer.transform(X_val_text)
    y_pred = svm.predict(X_val_vec)

    report = classification_report(
        y_val,
        y_pred,
        output_dict=True
    )

    f1_macro = f1_score(y_val, y_pred, average="macro")

    # Save SVM
    joblib.dump(svm, artifacts_dir / "svm.joblib")

    return {
        "f1_macro": f1_macro,
        "classification_report": report,
        "tfidf_path": artifacts_dir / "tfidf.joblib",
        "svm_path": artifacts_dir / "svm.joblib",
    }
