FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# git requis par DVC pour pull
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies
COPY requirements-common.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy application code
COPY config ./config
COPY src ./src

# DVC remote config (URL DagsHub uniquement, sans credentials)
COPY .dvc/config .dvc/config

# Create logs directory
RUN mkdir -p /app/logs /app/data/processed /app/models

# Run training script
CMD ["python", "-u", "src/training/train.py"]