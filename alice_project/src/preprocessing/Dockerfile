FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# git requis par DVC pour add/push
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git init /app

# Copy dependencies
COPY requirements-common.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy application code
COPY config ./config
COPY src ./src

# DVC remote config (URL DagsHub uniquement, sans credentials)
# Les credentials DAGSHUB_USERNAME / DAGSHUB_USER_TOKEN sont passés
# en variables d'environnement au runtime par le DAG Airflow
COPY .dvc/config .dvc/config

# Répertoires de travail
RUN mkdir -p /app/logs /app/data/raw /app/data/processed

# Run preprocessing script
CMD ["python", "-u", "src/preprocessing/run.py"]