from pathlib import Path
import pandas as pd

from src.features.build_features import (
    train_tfidf_vectorizer,
    load_tfidf_vectorizer,
    transform_texts,
)


def test_tfidf_training_and_transform(tmp_path):
    # Fake dataset
    df = pd.DataFrame({
        "text_clean": [
            "produit test",
            "autre produit",
            "encore un produit"
        ]
    })

    data_path = tmp_path / "data.csv"
    df.to_csv(data_path, index=False)

    vec_path = tmp_path / "tfidf.joblib"

    X, vectorizer = train_tfidf_vectorizer(
        data_path=data_path,
        output_path=vec_path,
        max_features=10
    )

    assert X.shape[0] == 3
    assert vec_path.exists()

    loaded_vectorizer = load_tfidf_vectorizer(vec_path)
    X_new = transform_texts(["nouveau produit"], loaded_vectorizer)

    assert X_new.shape[0] == 1
