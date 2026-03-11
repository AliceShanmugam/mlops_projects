# Architecture Rakuten MLOps

## Vue d'ensemble
┌─────────────────────────────────────────────────────────┐
│ GitHub Actions CI/CD Pipeline │
│ Tests → Lint → Security → Build → Push DockerHub │
└─────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────┐
│ Docker-Compose Production │
│ ┌──────────────┬──────────────┬──────────────────┐ │
│ │ MLFlow │ Airflow │ PostgreSQL │ │
│ │ :5000 │ :8081 │ :5432 │ │
│ └──────────────┴──────────────┴──────────────────┘ │
│ ┌──────────────┬──────────────┬──────────────────┐ │
│ │ Preprocessing│ Training │ API (x3) │ │
│ │ :8002 │ :8001 │ :8000 (LB) │ │
│ └──────────────┴──────────────┴───────────────────┘ │
│ ┌──────────────┬──────────────────────────────────┐ │
│ │ Prometheus │ Grafana │ │
│ │ :9090 │ :3000 │ │
│ └──────────────┴──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Pipeline d'orchestration (Airflow DAG)
RAW_DATA
↓
[preprocess] → [train] → [evaluate] → [package] → [notify]
↓ ↓ ↓ ↓
Logs MLFlow Metrics Registry

API Endpoints
Public
GET /health - Health check
Protected (require API-Key)
POST /predict - Text prediction
POST /training/trigger - Trigger training pipeline
GET /training/status/{dag_run_id} - Get training status
GET /training/logs/{dag_run_id} - Get training logs



┌─────────────────────────────────────────┐
│ Gateway (toujours prêt à servir)        │
│ - Reçoit requêtes                       │
│ - Déclenche entraînement via API        │
│ - NE BLOQUE PAS                         │
└─────────────────────────────────────────┘
              ↓ POST /training/trigger
┌─────────────────────────────────────────┐
│ Airflow Webserver                       │
│ - Reçoit le trigger                     │
│ - Lance DAG training_pipeline           │
│ - Orchester: preprocess → train → eval  │
└─────────────────────────────────────────┘
              ↓ (async)
┌─────────────────────────────────────────┐
│ Airflow Scheduler (Docker ops)          │
│ - Task 1: preprocess (container)        │
│ - Task 2: train (container)             │
│ - Task 3: evaluate (container)          │
│ - Task 4: package (container)           │
└─────────────────────────────────────────┘

User: curl "Check status on Airflow Dashboard :8081"