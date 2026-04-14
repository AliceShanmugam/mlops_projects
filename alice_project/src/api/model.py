"""
Model loading and prediction
"""

import joblib
import os
from config.logging_config import get_logger
from src.utils.exceptions import ModelNotFoundError, PredictionError

logger = get_logger(__name__)

# Get model paths from config or environment
MODELS_PATH = os.getenv("MODELS_PATH", "/app/models")
if not os.path.exists(MODELS_PATH):
    MODELS_PATH = "models"

tfidf_path = os.path.join(MODELS_PATH, os.getenv("TFIDF_MODEL", "tfidf_vectorizer.joblib"))
svm_path   = os.path.join(MODELS_PATH, os.getenv("SVM_MODEL",   "svm.joblib"))

# Poids de fusion texte vs image (texte prioritaire)
TEXT_WEIGHT  = float(os.getenv("TEXT_MODEL_WEIGHT",  "0.7"))
IMAGE_WEIGHT = float(os.getenv("IMAGE_MODEL_WEIGHT", "0.3"))

logger.info(f"Loading models from: {MODELS_PATH}")

# Load text model
try:
    tfidf_vectorizer = joblib.load(tfidf_path)
    svm_model        = joblib.load(svm_path)
    TEXT_MODEL_OK = True
    logger.info(f"✓ Text model loaded (tfidf + svm)")
except Exception as e:
    TEXT_MODEL_OK    = False
    tfidf_vectorizer = None
    svm_model        = None
    logger.warning(f"✗ Text model unavailable: {e}")

# Load image model
# Le modèle image n'est pas encore entraîné — placeholder
IMAGE_MODEL_OK = False
image_model    = None
logger.info("✗ Image model not yet trained — will use text-only fallback")

def predict_text(text: str) -> int:
    """Prédit via le modèle texte (TF-IDF + SVM)."""
    if not TEXT_MODEL_OK:
        raise PredictionError("Modèle texte non disponible")
    try:
        vec = tfidf_vectorizer.transform([text])
        return int(svm_model.predict(vec)[0])
    except Exception as e:
        raise PredictionError(f"Text prediction failed: {e}") from e


def predict_image(image_path: str) -> int:
    """Prédit via le modèle image (CNN — non implémenté)."""
    if not IMAGE_MODEL_OK:
        raise PredictionError("Modèle image non disponible")
    # TODO: implémenter quand train_image.py sera prêt
    raise PredictionError("Modèle image non implémenté")

def predict_combined(text: str = None, image_path: str = None) -> dict:
    """
    Prédit en combinant texte et image.
    - Si les deux sont disponibles : fusion pondérée (text=0.7, image=0.3)
    - Si un seul fonctionne : fallback sur ce modèle avec flag fallback=True
    - Si aucun ne fonctionne : lève PredictionError
    """
    text_label  = None
    image_label = None
    text_error  = None
    image_error = None

    if text:
        try:
            text_label = predict_text(text)
        except PredictionError as e:
            text_error = str(e)
            logger.warning(f"Text model failed: {e}")

    if image_path:
        try:
            image_label = predict_image(image_path)
        except PredictionError as e:
            image_error = str(e)
            logger.warning(f"Image model failed: {e}")

    # Cas 1 : les deux ont fonctionné → fusion pondérée
    # (même label → direct ; labels différents → on prend le plus pondéré)
    if text_label is not None and image_label is not None:
        if text_label == image_label:
            final_label = text_label
        else:
            # Le texte a plus de poids → on prend sa prédiction
            final_label = text_label if TEXT_WEIGHT >= IMAGE_WEIGHT else image_label
        return {
            "label": final_label,
            "source": "combined",
            "text_label": text_label,
            "image_label": image_label,
            "fallback": False,
            "fallback_reason": None,
        }

    # Cas 2 : seul le texte a fonctionné
    if text_label is not None:
        return {
            "label": text_label,
            "source": "text",
            "text_label": text_label,
            "image_label": None,
            "fallback": image_path is not None,  # fallback si image était demandée
            "fallback_reason": image_error,
        }

    # Cas 3 : seule l'image a fonctionné
    if image_label is not None:
        return {
            "label": image_label,
            "source": "image",
            "text_label": None,
            "image_label": image_label,
            "fallback": text is not None,
            "fallback_reason": text_error,
        }

    # Cas 4 : aucun modèle n'a fonctionné
    raise PredictionError(
        f"Tous les modèles ont échoué. Texte: {text_error}. Image: {image_error}"
    )

def predict(text: str) -> int:
    return predict_combined(text=text)
    

def reload_models() -> None:
    """Recharge les modèles texte depuis le disque après promotion."""
    global tfidf_vectorizer, svm_model, TEXT_MODEL_OK
    try:
        tfidf_vectorizer = joblib.load(tfidf_path)
        svm_model        = joblib.load(svm_path)
        TEXT_MODEL_OK    = True
        logger.info(f"✅ Modèles texte rechargés depuis {MODELS_PATH}")
    except Exception as e:
        TEXT_MODEL_OK = False
        logger.error(f"❌ Reload échoué: {e}")
        raise