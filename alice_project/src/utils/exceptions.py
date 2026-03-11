"""
Exception definitions for Rakuten MLOps
"""


class RakutenMLOpsException(Exception):
    """Base exception for Rakuten MLOps"""
    pass


class ModelNotFoundError(RakutenMLOpsException):
    """Raised when model file is not found"""
    pass


class PredictionError(RakutenMLOpsException):
    """Raised when prediction fails"""
    pass


class DataValidationError(RakutenMLOpsException):
    """Raised when data validation fails"""
    pass


class TrainingError(RakutenMLOpsException):
    """Raised when training fails"""
    pass


class AuthenticationError(RakutenMLOpsException):
    """Raised when authentication fails"""
    pass


class RateLimitError(RakutenMLOpsException):
    """Raised when rate limit is exceeded"""
    pass