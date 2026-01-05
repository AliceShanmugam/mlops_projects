FROM python:3.12-slim

WORKDIR /mlflow

RUN pip install --no-cache-dir mlflow

CMD mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root /mlflow/mlruns \
  --serve-artifacts \
  --allowed-hosts "*" \
  --cors-allowed-origins "*"

