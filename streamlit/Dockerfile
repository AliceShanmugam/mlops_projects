FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit>=1.28.0 plotly requests

# Copier le code
COPY streamlit/ /app/
COPY data/ /app/data/ 2>/dev/null || true
COPY models/ /app/models/ 2>/dev/null || true

# Configuration Streamlit
RUN mkdir -p ~/.streamlit
RUN echo "[server]\nheadless = true\nport = 8501\nenableCORS = false\nenableXsrfProtection = true\n" > ~/.streamlit/config.toml

# Exposer le port
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Lancer l'app
CMD ["streamlit", "run", "streamlit_rakuten.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
