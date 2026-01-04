
    # src/preprocessing/text_cleaning.py
import re
import html
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

IMAGE_DIR = Path("data/raw/image_train")

# =========================
# Build image paths
# =========================
def add_image_paths(df: pd.DataFrame, image_dir: Path) -> pd.DataFrame:
    def build_path(row):
        filename = f"image_{row.imageid}_product_{row.productid}.jpg"
        path = image_dir / filename
        return str(path)

    df["image_path"] = df.apply(build_path, axis=1)
    return df
# =========================
# Label mapping Rakuten
# =========================
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

LABEL_NAME = {
    0: "jeux vidéo",
    1: "livres / magazines",
    2: "jeux de société",
    3: "maquettes / drones",
    4: "mobilier",
    5: "déco maison",
    6: "fournitures",
    7: "jardin / piscine",
}

# =========================
# Text cleaning
# =========================
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = text.lower()
    text = re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿñæœ ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_language_safe(text: str) -> str:
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
    detect_lang: bool = True,
) -> None:

    df_x = pd.read_csv(x_path)
    df_y = pd.read_csv(y_path)

    df = pd.concat([df_x, df_y], axis=1)

    # Merge text
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
    df["label_name"] = df["label"].map(LABEL_NAME)
    df = add_image_paths(df, IMAGE_DIR)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df[
        [
            "productid",
            "imageid",
            "text_clean",
            "label",
            "label_name",
            "image_path"
        ]
    ].to_csv(output_path, index=False)

