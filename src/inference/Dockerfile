FROM python:3.12-slim

WORKDIR /app

# 1. Installe les dépendances système pour PyTorch
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copie les requirements et installe les dépendances
COPY src/inference/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copie tout le code source
COPY src/ /app/src/

# 4. Variable d'environnement pour les imports
ENV PYTHONPATH=/app

# 5. Commande de démarrage
CMD ["uvicorn", "src.inference.main:app", "--host", "0.0.0.0", "--port", "8001"]

