FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Docker crée un dossier /app à l’intérieur du conteneur.
# Tous les chemins suivants dans le Dockerfile seront relatifs à /app.
# Pas besoin que /app existe sur le disque local, Docker le crée automatiquement dans l’image.
WORKDIR /app

# Dépendances

# Copie le fichier depuis ton disque local (le contexte de build) vers /app/ dans le conteneur.
COPY requirements.txt .
# Installe toutes les librairies dans l’image Docker (isolé de ton Python local).
# Le conteneur a maintenant tout l’environnement Python nécessaire pour exécuter le code.
RUN pip install --no-cache-dir -r requirements.txt

# Code
# Copie tout le dossier src/preprocessing/ depuis le disque local vers /app/src/preprocessing/ dans le conteneur.
COPY src/preprocessing/ ./

# Commande par défaut = pipeline complet
CMD ["python", "preprocessing.py"]