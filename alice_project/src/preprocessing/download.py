"""
Download raw data from challengedata.ens.fr and store locally in data/raw/.

Versioning strategy :
  - data/raw/ contient toujours la dernière version téléchargée
  - data/raw/lineage.json trace les métadonnées d'ingestion
  - Le versionnement DVC (dvc add data/raw/ && dvc push) est géré
    par GitHub Actions monthly.yml après l'exécution de ce script.
"""

import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://challengedata.ens.fr"
LOGIN_URL = f"{BASE_URL}/login/?next=/challenges/35"

FILES = {
    "X_train_update.xlsx": "/participants/challenges/35/download/x-train",
    "Y_train_CVw08PX.xlsx": "/participants/challenges/35/download/y-train",
    "X_test_update.xlsx":   "/participants/challenges/35/download/x-test",
}
# Dossier de sortie local — surchargeable via variable d'environnement
DATA_RAW_DIR = os.getenv("DATA_RAW_DIR", "data/raw")


def login(session: requests.Session) -> bool:
    """Authentification CSRF sur challengedata.ens.fr"""
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


def _write_lineage(download_date: str, file_sizes: dict) -> None:
    """Écrit data/raw/lineage.json pour tracer l'ingestion (data lineage)."""
    meta = {
        "download_date": download_date,
        "downloaded_at": datetime.now().isoformat(),
        "local_path": DATA_RAW_DIR,
        "files": {
            fname: {"size_bytes": size} for fname, size in file_sizes.items()
        },
    }
    lineage_path = os.path.join(DATA_RAW_DIR, "lineage.json")
    with open(lineage_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✅ lineage.json → {lineage_path}")


def download_all(download_date: str = None) -> str:
    """
    Télécharge les fichiers raw dans DATA_RAW_DIR (data/raw/ par défaut).

    Args:
        download_date: Étiquette YYYY-MM de la version (défaut : mois courant).
                       Stocké dans data/raw/lineage.json et /tmp/download_date.txt
                       pour les tâches Airflow aval.

    Returns:
        download_date utilisé.
    """
    if not download_date:
        download_date = datetime.now().strftime("%Y-%m")

    if not os.getenv("CHALLENGEDATA_USERNAME") or not os.getenv("CHALLENGEDATA_PASSWORD"):
        raise ValueError(
            "CHALLENGEDATA_USERNAME et CHALLENGEDATA_PASSWORD sont requis"
        )

    os.makedirs(DATA_RAW_DIR, exist_ok=True)

    session = requests.Session()
    print("🔐 Authentification sur challengedata.ens.fr...")
    login(session)
    print(f"✅ Connecté — version cible : {download_date}")

    file_sizes: dict = {}

    for filename, path in FILES.items():
        print(f"⬇️  Téléchargement de {filename}...")
        resp = session.get(f"{BASE_URL}{path}")
        resp.raise_for_status()

        dest = os.path.join(DATA_RAW_DIR, filename)
        with open(dest, "wb") as f:
            f.write(resp.content)

        file_sizes[filename] = len(resp.content)
        print(f"  ✅ → {dest} ({len(resp.content) / 1_000_000:.1f} MB)")

    _write_lineage(download_date, file_sizes)

    # Transmission de la date à la tâche preprocess Airflow
    with open("/tmp/download_date.txt", "w") as f:
        f.write(download_date)

    print(f"\n🎉 Download terminé. Version : {download_date}")
    return download_date


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download Rakuten data → data/raw/")
    parser.add_argument(
        "--download_date",
        default=os.getenv("DOWNLOAD_DATE"),
        help="Version YYYY-MM (défaut : mois courant, ou var env DOWNLOAD_DATE)",
    )
    args = parser.parse_args()
    download_all(download_date=args.download_date or None)