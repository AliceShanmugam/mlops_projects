
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# # =========================
# # CONSTANTS
# # =========================
# IMAGE_DIR = Path("data/raw/image_train")


# # =========================
# # IMAGE PATHS
# # =========================
# def add_image_paths(df: pd.DataFrame, image_dir: Path) -> pd.DataFrame:
#     if not {"imageid", "productid"}.issubset(df.columns):
#        df["image_path"] = None
#        return df
#     def build_path(row):
#         filename = f"image_{row.imageid}_product_{row.productid}.jpg"
#         path = image_dir / filename
#         return str(path) if path.exists() else None

#     df["image_path"] = df.apply(build_path, axis=1)
#     return df

# =========================
# TF-IDF TRAINING
# =========================
def train_tfidf_vectorizer(
    data_path: Path,
    artifacts_dir: Path,
    text_column: str = "text_clean",
    max_features: int = 50000,
    ngram_range: tuple = (1, 2)
):
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_path)

    texts = df[text_column].astype(str)

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=True,
    )

    X = vectorizer.fit_transform(texts)

    tfidf_path = artifacts_dir / "tfidf.joblib"
    joblib.dump(vectorizer, tfidf_path)

    print(f"TF-IDF saved to {tfidf_path}")

    return X, vectorizer
