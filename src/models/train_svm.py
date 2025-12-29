# from pathlib import Path
# import joblib
# import pandas as pd

# from sklearn.svm import LinearSVC
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import f1_score

# from src.features.build_features import (
#     train_tfidf_vectorizer,
#     load_tfidf_vectorizer,
#     transform_texts,
# )


# # =========================
# # Load processed data
# # =========================
# def load_processed_data(csv_path: Path):
#     df = pd.read_csv(csv_path)
#     X_text = df["text_clean"].astype(str)
#     y = df["label"].astype(int)
#     return X_text, y


# # =========================
# # Train SVM
# # =========================
# def train_svm(
#     X_features,
#     y,
#     C: float = 1.0,
# ):
#     model = LinearSVC(C=C)
#     model.fit(X_features, y)
#     return model


# # =========================
# # Train + Evaluate
# # =========================
# def train_and_evaluate_svm(
#     data_path: Path,
#     artifacts_dir: Path,
#     tfidf_params: dict | None = None,
#     svm_params: dict | None = None,
# ):
#     artifacts_dir.mkdir(parents=True, exist_ok=True)

#     tfidf_params = tfidf_params or {}
#     svm_params = svm_params or {}

#     # Load data
#     X_text, y = load_processed_data(data_path)

#     # Split
#     X_train_text, X_val_text, y_train, y_val = train_test_split(
#         X_text, y, test_size=0.2, random_state=42, stratify=y
#     )

#     # Train TF-IDF (fit ONLY on train)
#     X_train_vec, vectorizer = train_tfidf_vectorizer(
#         data_path=data_path,
#         output_path=artifacts_dir / "tfidf.joblib",
#         **tfidf_params,
#     )

#     # Train SVM
#     svm = train_svm(X_train_vec, y_train, **svm_params)

#     # Evaluate
#     X_val_vec = transform_texts(X_val_text, vectorizer)
#     y_pred = svm.predict(X_val_vec)
#     f1 = f1_score(y_val, y_pred, average="macro")

#     # Save model
#     joblib.dump(svm, artifacts_dir / "svm.joblib")

#     return {
#         "f1_macro": f1,
#         "tfidf_path": artifacts_dir / "tfidf.joblib",
#         "svm_path": artifacts_dir / "svm.joblib",
#     }

from pathlib import Path
import joblib
import pandas as pd

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

from src.features.build_features import (
    train_tfidf_vectorizer,
    transform_texts,
)


# =========================
# Load processed data
# =========================
def load_processed_data(csv_path: Path):
    df = pd.read_csv(csv_path)
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
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    tfidf_params = tfidf_params or {}
    svm_params = svm_params or {}

    # Load data
    X_text, y = load_processed_data(data_path)

    # Split
    X_train_text, X_val_text, y_train, y_val = train_test_split(
        X_text,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # === TF-IDF (fit only on train) ===
    X_train_vec, vectorizer = train_tfidf_vectorizer(
        data_path=data_path,
        output_path=artifacts_dir / "tfidf.joblib",
        **tfidf_params,
    )

    # === Train SVM ===
    svm = train_svm(X_train_vec, y_train, **svm_params)

    # === Evaluation ===
    X_val_vec = transform_texts(X_val_text, vectorizer)
    y_pred = svm.predict(X_val_vec)

    report = classification_report(
        y_val,
        y_pred,
        output_dict=True
    )

    f1_macro = f1_score(y_val, y_pred, average="macro")

    # Save artifacts
    joblib.dump(svm, artifacts_dir / "svm.joblib")

    return {
        "f1_macro": f1_macro,
        "classification_report": report,
        "tfidf_path": artifacts_dir / "tfidf.joblib",
        "svm_path": artifacts_dir / "svm.joblib",
    }
