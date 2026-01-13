# Script principal

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from preprocessing import clean_text
from model import build_svm_pipeline
from evaluate import evaluate_model


DATA_PATH = "data/processed/df_labeled_fr.csv"
TEXT_COL = "text"
TARGET_COL = "label"
MODEL_OUTPUT = "models/model.pkl"


def main():
    # Load data
    df = pd.read_csv(DATA_PATH)

    df[TEXT_COL] = df[TEXT_COL].astype(str).apply(clean_text)

    X = df[TEXT_COL]
    y = df[TARGET_COL]

    # Encode labels
    label_encoder = LabelEncoder()
    y_enc = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    results = {}

    # ------------------
    # SVM
    svm_pipeline = build_svm_pipeline()
    svm_pipeline.fit(X_train, y_train)
    svm_preds = svm_pipeline.predict(X_test)

    results["svm"] = evaluate_model(y_test, svm_preds)

    # Save model + label encoder
    joblib.dump(
        {
            "model": svm_pipeline,
            "label_encoder": label_encoder
        },
        MODEL_OUTPUT
    )


if __name__ == "__main__":
    main()