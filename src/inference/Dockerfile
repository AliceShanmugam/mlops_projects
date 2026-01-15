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

# 3. Copie le fichier main.py
COPY src/inference/main.py .

# 4. Copie les fichiers nécessaires depuis src/ (pour SimpleCNN)
COPY src/train_models/train_cnn.py src/train_models/

# 5. Variable d'environnement pour les imports
ENV PYTHONPATH=/app

# 6. Commande de démarrage
CMD ["uvicorn", "src.inference.main:app", "--host", "0.0.0.0", "--port", "8000"]

