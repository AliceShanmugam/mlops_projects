# 🚀 Roadmap MLOps - Alice Project

## 1️⃣ FONDATIONS (Logging + Architecture)

### 1.1 Logging Centralisé
**Objectif**: Traçabilité complète du pipeline
- [ ] Setup logging structuré (structlog)
- [ ] Configuration globale (config/logging.py)
- [ ] Logs dans tous les services (preprocessing, training, API, Airflow)
- [ ] Format JSON pour agrégation
- [ ] Rotation des logs

**Impact**: Transversal - essentiellement pour debug et monitoring

### 1.2 Architecture Refactorisée
- [ ] Dossier `config/` avec configurations centralisées
- [ ] Dossier `utils/` avec helpers partagés
- [ ] Dossier `schemas/` pour modèles Pydantic centralisés
- [ ] Variables d'environnement (.env)

**Impact**: Permet Phase 2 CI/CD

---

## 2️⃣ ORCHESTRATION (Airflow + Async API)

### 2.1 Airflow DAG Complet
**Pipeline**: RAW_DATA → PREPROCESS → TRAIN → EVALUATE → PACKAGE → PUSH_REGISTRY

```
preprocessing → training → evaluation → packaging → registry_push
```

- [ ] DAG `training_pipeline.py` avec dépendances
- [ ] Configuration DockerOperator correctly (networks, volumes)
- [ ] Airflow DB init dans docker-compose
- [ ] Créer un backend approprié (PostgreSQL recommandé)

### 2.2 API de Déclenchement Async
- [ ] Endpoint `/training/trigger` - lance DAG Airflow
- [ ] Endpoint `/training/status/{run_id}` - récupère statut
- [ ] Endpoint `/training/logs/{run_id}` - récupère logs
- [ ] Gestion des erreurs

**Dépendances**: `apache-airflow` API client

---

## 3️⃣ SÉCURITÉ API

### 3.1 Authentication & Authorization
- [ ] API Key simple (Bearer token)
- [ ] Validation de permission par endpoint
- [ ] JWT optionnel si scaling

### 3.2 Rate Limiting & Validation
- [ ] Rate limiter middleware (slowapi)
- [ ] Input validation strict (Pydantic)
- [ ] CORS configuration
- [ ] Error sanitization (ne pas exposer stack traces)

### 3.3 API Hardening
- [ ] Timeout requests
- [ ] Response compression
- [ ] Security headers
- [ ] Request logging (sans données sensibles)

---

## 4️⃣ CI/CD PIPELINE (GitHub Actions)

### 4.1 Workflow Tests
```yaml
Tests:
  - Python tests (pytest)
  - Lint (pylint, flake8)
  - Security scan (bandit)
  - Docker build test
```

### 4.2 Workflow Build & Push
```yaml
Build:
  - Build images: preprocessing, training, api, gateway
  - Push to DockerHub
  - Tag avec: version-git-hash
```

### 4.3 Versioning Strategy
- [ ] Semantic Versioning (0.1.0)
- [ ] Git tags per release
- [ ] Model registry avec MLFlow
- [ ] Data versioning (DVC ou timestamps)

---

## 5️⃣ MONITORING & DRIFT

### 5.1 Model Monitoring
- [ ] Récupérer predictions → enregistrer dans DB
- [ ] Comparer predictions vs actuals (si disponible)
- [ ] Détecter data drift (distributions)
- [ ] Créer alertes si drift > threshold

### 5.2 API Monitoring
- [ ] Latency tracking (Prometheus)
- [ ] Error rate tracking
- [ ] Request volume tracking
- [ ] Health check endpoint

### 5.3 Infrastructure Monitoring
- [ ] Container health checks
- [ ] Disk usage
- [ ] Memory usage

---

## 6️⃣ SCALABILITÉ SIMPLE (Docker)

### 6.1 Load Balancing
- [ ] Nginx reverse proxy
- [ ] Plusieurs replicas API (docker-compose scale)
- [ ] Sticky sessions si nécessaire

### 6.2 Persistence
- [ ] PostgreSQL pour Airflow (vs SQLite)
- [ ] Redis pour caching optionnel
- [ ] Volumes pour modèles

### 6.3 Container Orchestration
- [ ] Docker-compose v3+ avec restart policies
- [ ] Health checks dans Dockerfiles
- [ ] Resource limits

---

## 7️⃣ REPRODUCIBILITÉ & PROOF

### 7.1 Versioning
- [ ] Modèles tagués dans MLFlow + DockerHub
- [ ] Data snapshots (timestamps folders)
- [ ] Requirements.txt + pip freeze
- [ ] Dockerfile pinned versions

### 7.2 Testing
- [ ] Test data fixtures reproductibles
- [ ] Test de pipeline complet
- [ ] Test d'inférence (même résultat)
- [ ] Integration tests avec docker-compose

### 7.3 Documentation
- [ ] Architecture diagram (Mermaid)
- [ ] Setup guide (1 commande = déploiement)
- [ ] API documentation (Swagger auto)
- [ ] Airflow DAG visualization

---

## Timeline Proposée

| Phase | Durée | Tâches |
|-------|-------|--------|
| 1 | 2-3h | Logging + Config architecture |
| 2 | 3-4h | Airflow DAG + Async API |
| 3 | 2-3h | Sécurité API |
| 4 | 3-4h | GitHub Actions CI/CD |
| 5 | 2-3h | Monitoring basique |
| 6 | 1-2h | Scalabilité Docker |
| 7 | 2-3h | Tests + Documentation |
| **Total** | **16-22h** | Projet complet |

---

## Quick Start Après Implémentation

```bash
# Setup environnement
git clone <repo>
cd alice_project

# Launch tout
docker-compose up -d

# Accès services
- Airflow UI: http://localhost:8081
- API: http://localhost:8000
- MLFlow: http://localhost:5000

# Trigger training
curl -X POST http://localhost:8000/training/trigger \
  -H "Authorization: Bearer YOUR_API_KEY"

# Watch DAG
# Allez sur Airflow UI → training_pipeline
```

---

## Priorités d'Implémentation

🔴 **CRITIQUE (Do First)**
1. Logging centralisé
2. Airflow DAG complet
3. API de déclenchement async

🟠 **IMPORTANT (Do Second)**
4. Sécurité API
5. GitHub Actions CI/CD

🟡 **NICE-TO-HAVE (Bonus)**
6. Monitoring avancé
7. Scalabilité
8. Drift detection

