import html
import io
import json
import os
from datetime import datetime

import joblib
import pandas as pd
import spacy
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, detect 
from langdetect.lang_detect_exception import LangDetectException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import openpyxl

DetectorFactory.seed = 0

DATA_RAW_DIR       = os.getenv("DATA_RAW_DIR", "data/raw")
DATA_PROCESSED_DIR = os.getenv("DATA_PROCESSED_DIR", "data/processed")

def clean_text(text: str) -> str:
    text = html.unescape(str(text))
    text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    return text.lower()

def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='fr').translate(text)
    except Exception:
        return text
    
LABEL_MAPPING = {
    0: [40, 50, 60],
    1: [10, 2705],
    2: [1160, 1281],
    3: [1300],
    4: [1560],
    5: [2060],
    6: [2522],
    7: [2582, 2585],
}

def _save_joblib(obj, path: str) -> None:
    joblib.dump(obj, path)
    print(f"  ✅ → {path}")

def _write_lineage(data_version: str, download_date: str, n_rows: int) -> None:
    """Écrit data/processed/lineage.json pour tracer la transformation."""
    meta = {
        "data_version": data_version,
        "download_date": download_date,
        "processed_at": datetime.now().isoformat(),
        "local_path": DATA_PROCESSED_DIR,
        "source_raw_path": DATA_RAW_DIR,
        "n_rows": n_rows,
    }
    lineage_path = os.path.join(DATA_PROCESSED_DIR, "lineage.json")
    with open(lineage_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✅ lineage.json → {lineage_path}")

def preprocess(run_translation=True):
    """
    Lit les données raw depuis DATA_RAW_DIR (data/raw/),
    applique le preprocessing et sauvegarde dans DATA_PROCESSED_DIR (data/processed/).

    Returns:
        data_version : timestamp YYYYMMDD_HHMMSS utilisé comme identifiant
                       de version pour les tâches Airflow aval (train.py).
    """
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

    # Lecture des données raw locales
    print(f"📂 Lecture des données raw depuis {DATA_RAW_DIR}/")
    df_products = pd.read_excel(os.path.join(DATA_RAW_DIR, "X_train_update.xlsx"))
    df_labels   = pd.read_excel(os.path.join(DATA_RAW_DIR, "Y_train_CVw08PX.xlsx"))
    
    # Récupération de la date de download depuis le lineage raw (pour traçabilité)
    download_date = "unknown"
    raw_lineage_path = os.path.join(DATA_RAW_DIR, "lineage.json")
    if os.path.exists(raw_lineage_path):
        with open(raw_lineage_path) as f:
            download_date = json.load(f).get("download_date", "unknown")

    df = pd.concat([df_products, df_labels], axis=1)
    df = df[['designation', 'description', 'productid', 'imageid', 'prdtypecode']]

    df['text'] = (
        df['designation'].fillna('').astype(str) + " " +
        df['description'].fillna('').astype(str)
    )

    df['text'] = df['text'].apply(clean_text)

    # Labelisation
    labeled_frames = []
    for label, codes in LABEL_MAPPING.items():
        temp = df[df['prdtypecode'].isin(codes)].copy()
        temp['label'] = label
        labeled_frames.append(temp)

    df_labeled = pd.concat(labeled_frames).reset_index(drop=True)
    print(f"✅ {len(df_labeled)} lignes labélisées")

    # Langue
    df_labeled['langue'] = df_labeled['text'].apply(detect_language)
    df_labeled['text_fr'] = df_labeled['text']

    if run_translation:
        mask = (df_labeled['langue'] != 'fr') & (df_labeled['langue'] != 'unknown') & (df_labeled['text'].str.strip() != "")
        tqdm.pandas(desc="Traduction FR")
        df_labeled.loc[mask, 'text_fr'] = df_labeled.loc[mask, 'text'].progress_apply(translate_text)

    # Split des données
    X = df_labeled['text_fr']
    y = df_labeled['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Stopwords
    nlp = spacy.blank("fr")
    french_stopwords = list(nlp.Defaults.stop_words)

    # Vectorisation TF-IDF
    tfidf_vectorizer = TfidfVectorizer(
    stop_words=french_stopwords,
    max_features=2000,
    ngram_range=(1, 2),
    )

    X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
    X_test_tfidf = tfidf_vectorizer.transform(X_test)

    # Sauvegarde des jeux de données prétraités
    data_version = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n💾 Sauvegarde dans {DATA_PROCESSED_DIR}/ (version: {data_version})")

    _save_joblib(X_train_tfidf,    os.path.join(DATA_PROCESSED_DIR, "X_train_tfidf.joblib"))
    _save_joblib(X_test_tfidf,     os.path.join(DATA_PROCESSED_DIR, "X_test_tfidf.joblib"))
    _save_joblib(y_train,          os.path.join(DATA_PROCESSED_DIR, "y_train.joblib"))
    _save_joblib(y_test,           os.path.join(DATA_PROCESSED_DIR, "y_test.joblib"))
    _save_joblib(tfidf_vectorizer, os.path.join(DATA_PROCESSED_DIR, "tfidf_vectorizer.joblib"))
    
    _write_lineage(data_version, download_date, len(df_labeled))

    return data_version

if __name__ == "__main__":
    preprocess(run_translation=True)