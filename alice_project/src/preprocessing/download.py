"""
Download raw data from challengedata.ens.fr and store in MinIO
"""
import os
import io
import boto3
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://challengedata.ens.fr"
LOGIN_URL = f"{BASE_URL}/login/?next=/challenges/35"

FILES = {
    "X_train_update.xlsx": "/participants/challenges/35/download/x-train",
    "Y_train_CVw08PX.xlsx": "/participants/challenges/35/download/y-train",
    "X_test_update.xlsx":   "/participants/challenges/35/download/x-test",
}


def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio:9000'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )


def login(session: requests.Session) -> bool:
    """Authentification avec CSRF token Django"""
    # 1. Récupérer la page de login pour obtenir le CSRF token
    resp = session.get(LOGIN_URL)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if not csrf:
        raise ValueError("CSRF token introuvable sur la page de login")

    # 2. Envoyer les credentials
    payload = {
        "csrfmiddlewaretoken": csrf["value"],
        "username": os.getenv("CHALLENGEDATA_USERNAME"),
        "password": os.getenv("CHALLENGEDATA_PASSWORD"),
    }
    headers = {"Referer": LOGIN_URL}
    resp = session.post(LOGIN_URL, data=payload, headers=headers)
    resp.raise_for_status()

    # 3. Vérifier que le login a réussi (redirection vers /challenges/35)
    if "login" in resp.url:
        raise ValueError("Authentification échouée — vérifiez username/password")

    return True


def download_to_minio(session: requests.Session, s3, filename: str, path: str):
    """Télécharge un fichier et l'upload directement dans MinIO"""
    url = f"{BASE_URL}{path}"
    resp = session.get(url, stream=True)
    resp.raise_for_status()

    # Upload stream vers MinIO sans écrire sur disque
    if filename == "X_train_update.xlsx":
        df = pd.read_excel(io.BytesIO(resp.content))
        n = len(df)

        for batch_name, batch_df in [
            ("X_train_batch_1.xlsx", df[:n//2]),
            ("X_train_batch_2.xlsx", df[n//2:]),
        ]:
            buf = io.BytesIO()
            batch_df.to_excel(buf, index=False)
            buf.seek(0)
            s3.upload_fileobj(buf, "raw-data", batch_name)
            print(f"✅ {batch_name} → MinIO bucket raw-data")
    else:
        file_obj = io.BytesIO(resp.content)
        s3.upload_fileobj(file_obj, "raw-data", filename)
        print(f"✅ {filename} → MinIO bucket raw-data")


def download_all():
    username = os.getenv("CHALLENGEDATA_USERNAME")
    password = os.getenv("CHALLENGEDATA_PASSWORD")
    if not username or not password:
        raise ValueError("CHALLENGEDATA_USERNAME et CHALLENGEDATA_PASSWORD requis dans .env")

    s3 = get_s3_client()
    session = requests.Session()

    print("🔐 Authentification sur challengedata.ens.fr...")
    login(session)
    print("✅ Connecté")

    for filename, path in FILES.items():
        print(f"⬇️  Téléchargement de {filename}...")
        download_to_minio(session, s3, filename, path)

    print("🎉 Tous les fichiers téléchargés dans MinIO bucket raw-data")


if __name__ == "__main__":
    download_all()