"""
Application settings and configuration
Load from environment variables with defaults
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application configuration"""
    
    # Application
    APP_NAME: str = "Alice MLOps"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_KEY: str = os.getenv("API_KEY", "dev-key-insecure")
    
    # MLFlow
    MLFLOW_TRACKING_URI: str = os.getenv(
        "MLFLOW_TRACKING_URI", 
        "http://mlflow:5000"
    )
    
    # Airflow
    AIRFLOW_WEBSERVER_URL: str = os.getenv(
        "AIRFLOW_WEBSERVER_URL",
        "http://airflow:8080"
    )
    AIRFLOW_BASE_URL: str = os.getenv(
        "AIRFLOW_BASE_URL",
        "http://airflow-webserver:8080/api/v1"
    )
    
    # Data paths
    DATA_RAW_PATH: str = os.getenv("DATA_RAW_PATH", "/app/data/raw")
    DATA_PROCESSED_PATH: str = os.getenv("DATA_PROCESSED_PATH", "/app/data/processed")
    MODELS_PATH: str = os.getenv("MODELS_PATH", "/app/models")
    
    # Models
    TFIDF_MODEL: str = os.getenv("TFIDF_MODEL", "tfidf_vectorizer.joblib")
    SVM_MODEL: str = os.getenv("SVM_MODEL", "svm.joblib")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "/app/logs")
    JSON_LOGS: bool = os.getenv("JSON_LOGS", "false").lower() == "true"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # CORS - use field with default_factory for mutable defaults
    CORS_ORIGINS: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080"
    ])
    
    @property
    def tfidf_path(self) -> str:
        """Full path to TF-IDF model"""
        return os.path.join(self.MODELS_PATH, self.TFIDF_MODEL)
    
    @property
    def svm_path(self) -> str:
        """Full path to SVM model"""
        return os.path.join(self.MODELS_PATH, self.SVM_MODEL)


# Global settings instance
settings = Settings()