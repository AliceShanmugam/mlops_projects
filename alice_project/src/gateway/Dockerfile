FROM python:3.10-slim

WORKDIR /app

# Copy requirement files
COPY requirements-common.txt requirements-api.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY config ./config
COPY src ./src

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8080

CMD ["uvicorn", "src.gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]