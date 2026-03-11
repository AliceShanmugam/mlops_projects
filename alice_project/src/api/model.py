"""
Model loading and prediction
"""

import joblib
import os
from pathlib import Path
from config.logging_config import get_logger
from src.utils.exceptions import ModelNotFoundError, PredictionError

logger = get_logger(__name__)

# Get model paths from config or environment
MODELS_PATH = os.getenv("MODELS_PATH", "/app/models")
TFIDF_MODEL = os.getenv("TFIDF_MODEL", "tfidf_vectorizer.joblib")
SVM_MODEL = os.getenv("SVM_MODEL", "svm.joblib")

# Fallback to relative path for local development
if not os.path.exists(MODELS_PATH):
    MODELS_PATH = "models"

tfidf_path = os.path.join(MODELS_PATH, TFIDF_MODEL)
svm_path = os.path.join(MODELS_PATH, SVM_MODEL)

logger.info(f"Loading models from: {MODELS_PATH}")

# Load models at startup
try:
    tfidf_vectorizer = joblib.load(tfidf_path)
    logger.info(f"✓ TFIDF loaded from {tfidf_path}")
except FileNotFoundError as e:
    logger.error(f"✗ TFIDF model not found at {tfidf_path}")
    raise ModelNotFoundError(f"TFIDF model not found: {tfidf_path}") from e

try:
    svm_model = joblib.load(svm_path)
    logger.info(f"✓ SVM loaded from {svm_path}")
except FileNotFoundError as e:
    logger.error(f"✗ SVM model not found at {svm_path}")
    raise ModelNotFoundError(f"SVM model not found: {svm_path}") from e


def predict(text: str) -> int:
    """
    Predict label for given text
    Args:
        text: Input text to classify
    Returns:
        Predicted label (int)
    Raises:
        PredictionError: If prediction fails
    """
    try:
        logger.debug(f"Predicting for text: {text[:50]}...")
        
        # Transform text with TF-IDF
        text_vector = tfidf_vectorizer.transform([text])
        
        # Predict with SVM
        prediction = svm_model.predict(text_vector)[0]
        
        logger.debug(f"Prediction result: {prediction}")
        return int(prediction)
    
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        raise PredictionError(f"Prediction failed: {str(e)}") from e