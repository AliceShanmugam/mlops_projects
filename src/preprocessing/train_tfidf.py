
from pathlib import Path
import joblib
import pandas as pd
import mlflow
from sklearn.feature_extraction.text import TfidfVectorizer

mlflow.set_tracking_uri("sqlite:///src/mlflow/mlflow.db")
# =========================
# TF-IDF TRAINING
# =========================
def train_tfidf_vectorizer(
    data_path: Path,
    artifacts_dir: Path,
    text_column: str = "text_clean",
    max_features: int = 50000,
    ngram_range: tuple = (1, 2),
    experiment_name : str = "TFIDF_vectorizer",
    run_name : str ="TFIDF_run_1"
):
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name, nested=True):
        
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(data_path)
        texts = df[text_column].astype(str)
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True)

        X = vectorizer.fit_transform(texts)
        tfidf_path = artifacts_dir / "tfidf.joblib"
        joblib.dump(vectorizer, tfidf_path)
        # mlflow save tfidf maodel
        mlflow.log_artifact(tfidf_path,"vectorization")
        # mlflow Log parameters
        mlflow.log_param("num_texts", len(texts))   
        mlflow.log_param("avg_text_length", texts.str.len().mean())
        #mlflow.log_params("max_features", str(max_features))
        mlflow.log_param("ngram_range",str(ngram_range))
        mlflow.log_param("sublinear_tf", True)
        mlflow.log_param("text_column",text_column)
        #mlflow log metrics
        mlflow.log_metric("n_documents",X.shape[0])
        mlflow.log_metric("vocab_size",len(vectorizer.vocabulary_))
        mlflow.log_metric("sparsity",(X.nnz/(X.shape[0]*X.shape[1])))
        
        print(f"TF-IDF model saved to {tfidf_path}")
        return X, vectorizer
