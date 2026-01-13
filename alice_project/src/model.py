# Pipelines et entrainement du modèle

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC


def build_svm_pipeline():
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(
                max_features=2000,
                ngram_range=(1, 2),
                stop_words="english"
            )),
            ("clf", LinearSVC())
        ]
    )