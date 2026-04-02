FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV MLFLOW_S3_ENDPOINT_URL=${MINIO_ENDPOINT}

WORKDIR /app

# Copy dependencies
COPY requirements-common.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy application code
COPY config ./config
COPY src ./src

# Create logs directory
RUN mkdir -p /app/logs

# Run preprocessing script
CMD ["python", "-u", "src/preprocessing/run.py"]