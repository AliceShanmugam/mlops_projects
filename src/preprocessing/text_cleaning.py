import re
import html
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup


try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    DetectorFactory.seed = 0
    LANG_DETECT_AVAILABLE = True
except ImportError:
    LANG_DETECT_AVAILABLE = False


# =========================
# Label mapping Rakuten
# =========================
LABEL_MAPPING = {
    0: [40, 50, 60],          # jeux vidéo
    1: [10, 2705],            # livres / magazines
    2: [1160, 1281],          # jeux de société
    3: [1300],                # maquettes / drones
    4: [1560],                # mobilier
    5: [2060],                # déco maison
    6: [2522],                # fournitures
    7: [2582, 2585],          # jardin / piscine
}


# =========================
# Text cleaning
# =========================
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = html.unescape(text)
    text = BeautifulSoup(text, "html.parser").get_text(
        separator=" ", strip=True
    )
    text = text.lower()
    text = re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿñæœ ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_language(text: str) -> str:
    if not LANG_DETECT_AVAILABLE:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


# =========================
# Main preprocessing
# =========================
def preprocess_training_data(
    x_path: Path,
    y_path: Path,
    output_path: Path,
    detect_lang: bool = False,
) -> None:
    """
    Preprocess Rakuten training data:
    - merge X / y
    - clean text
    - map labels
    """

    df_x = pd.read_csv(x_path)
    df_y = pd.read_csv(y_path)

    df = pd.concat([df_x, df_y], axis=1)

    # Merge text fields
    df["text"] = (
        df["designation"].fillna("") + " " +
        df["description"].fillna("")
    )

    df["text_clean"] = df["text"].apply(clean_text)

    # Label mapping
    def map_label(prdtypecode):
        for label, codes in LABEL_MAPPING.items():
            if prdtypecode in codes:
                return label
        return None

    df["label"] = df["prdtypecode"].apply(map_label)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    # Optional language detection
    if detect_lang:
        df["language"] = df["text_clean"].apply(detect_language)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df[
        ["productid", "imageid", "text_clean", "label"]
        + (["language"] if detect_lang else [])
    ].to_csv(output_path, index=False)
