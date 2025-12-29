from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


# =========================
# Train TF-IDF
# =========================
def train_tfidf_vectorizer(
    data_path: Path,
    output_path: Path,
    text_column: str = "text_clean",
    max_features: int = 50000,
    ngram_range: tuple = (1, 2),
) :
    """
    Fit a TF-IDF vectorizer on training data and save it.

    Parameters
    ----------
    data_path : Path
        CSV file containing cleaned text.
    output_path : Path
        Path where the trained vectorizer will be saved.
    """

    df = pd.read_csv(data_path)

    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in dataset")

    texts = df[text_column].astype(str)

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=True,
    )

    X = vectorizer.fit_transform(texts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, output_path)

    return X, vectorizer


# =========================
# Load TF-IDF
# =========================
def load_tfidf_vectorizer(vectorizer_path: Path):
    """
    Load a trained TF-IDF vectorizer.
    """
    return joblib.load(vectorizer_path)


# =========================
# Transform new texts
# =========================
def transform_texts(
    texts,
    vectorizer
):
    """
    Transform raw texts using a fitted TF-IDF vectorizer.
    """
    return vectorizer.transform(texts)
