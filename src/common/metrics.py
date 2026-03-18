# src/common/metrics.py
"""
Prometheus metrics for API monitoring.
Request counts, latencies, errors, model-specific metrics.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from functools import wraps


# Create a custom registry for each service
def create_metrics_registry():
    """Create Prometheus metrics registry."""
    registry = CollectorRegistry()

    # Request metrics
    request_count = Counter(
        "mlops_requests_total",
        "Total API requests",
        ["service", "endpoint", "method", "status"],
        registry=registry,
    )

    request_latency = Histogram(
        "mlops_request_duration_seconds",
        "Request latency in seconds",
        ["service", "endpoint", "method"],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0),
        registry=registry,
    )

    # Model metrics
    model_predictions = Counter(
        "mlops_model_predictions_total",
        "Total predictions by model",
        ["service", "model_type"],
        registry=registry,
    )

    model_prediction_latency = Histogram(
        "mlops_model_prediction_duration_seconds",
        "Model prediction latency",
        ["service", "model_type"],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
        registry=registry,
    )

    # Model performance
    model_accuracy = Gauge(
        "mlops_model_accuracy",
        "Current model accuracy",
        ["service", "model_type"],
        registry=registry,
    )

    # Error metrics
    errors = Counter(
        "mlops_errors_total",
        "Total errors",
        ["service", "error_type"],
        registry=registry,
    )

    # Data drift metrics
    data_drift_score = Gauge(
        "mlops_data_drift_score",
        "Data drift score (0-1)",
        ["service", "feature"],
        registry=registry,
    )

    return {
        "registry": registry,
        "request_count": request_count,
        "request_latency": request_latency,
        "model_predictions": model_predictions,
        "model_prediction_latency": model_prediction_latency,
        "model_accuracy": model_accuracy,
        "errors": errors,
        "data_drift_score": data_drift_score,
    }


def track_request(service_name: str, endpoint: str, metrics: dict):
    """Decorator to track request metrics."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, "status_code", 500)
                raise
            finally:
                duration = time.time() - start_time
                metrics["request_count"].labels(
                    service=service_name,
                    endpoint=endpoint,
                    method="POST",
                    status=status_code,
                ).inc()
                metrics["request_latency"].labels(
                    service=service_name,
                    endpoint=endpoint,
                    method="POST",
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, "status_code", 500)
                raise
            finally:
                duration = time.time() - start_time
                metrics["request_count"].labels(
                    service=service_name,
                    endpoint=endpoint,
                    method="POST",
                    status=status_code,
                ).inc()
                metrics["request_latency"].labels(
                    service=service_name,
                    endpoint=endpoint,
                    method="POST",
                ).observe(duration)

        if hasattr(func, "__await__"):
            return async_wrapper
        return sync_wrapper

    return decorator
