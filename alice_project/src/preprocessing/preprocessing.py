
import pandas as pd
from bs4 import BeautifulSoup
import html
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from deep_translator import GoogleTranslator
from tqdm import tqdm
import os
from datetime import datetime 

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import spacy
import io
import boto3

DetectorFactory.seed = 0

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

def _upload_joblib(s3, obj, bucket: str, key: str):
    buf = io.BytesIO()
    joblib.dump(obj, buf)
    buf.seek(0)
    s3.upload_fileobj(buf, bucket, key)


def preprocess(run_translation=True):
    batch = int(os.getenv("BATCH", "1"))
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio:9000'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )

    # Lire batch 1..N et concaténer
    frames = []
    for i in range(1, batch + 1):
        df_b = pd.read_excel(io.BytesIO(
            s3.get_object(Bucket='raw-data', Key=f'X_train_batch_{i}.xlsx')['Body'].read()
        ))
        frames.append(df_b)
    df_products = pd.concat(frames, ignore_index=True)

    df_labels = pd.read_excel(io.BytesIO(
        s3.get_object(Bucket='raw-data', Key='Y_train_CVw08PX.xlsx')['Body'].read()
    ))

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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{timestamp}/"
    _upload_joblib(s3, X_train_tfidf,    'processed-data', f"{prefix}X_train_tfidf.joblib")
    _upload_joblib(s3, X_test_tfidf,     'processed-data', f"{prefix}X_test_tfidf.joblib")
    _upload_joblib(s3, y_train,          'processed-data', f"{prefix}y_train.joblib")
    _upload_joblib(s3, y_test,           'processed-data', f"{prefix}y_test.joblib")
    _upload_joblib(s3, tfidf_vectorizer, 'processed-data', f"{prefix}tfidf_vectorizer.joblib")
    
    return timestamp

if __name__ == "__main__":
    preprocess(run_translation=True)