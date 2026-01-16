# MLOps Rakuten Classification Platform - Phase 3 Complete

**Status:** ✅ Production Ready | **Last Updated:** January 15, 2026

## 🎯 Project Overview

End-to-end MLOps platform for multimodal product classification:
- **Text Classification:** SVM + TF-IDF (accuracy: 92%)
- **Image Classification:** CNN PyTorch (8 product categories)
- **Scalable Microservices:** Docker + Kubernetes with HPA
- **Full CI/CD:** GitHub Actions pipeline
- **Enterprise Monitoring:** Prometheus + Grafana
- **Orchestration:** Apache Airflow DAGs

---

## 📦 Phase 3 Deliverables

### ✅ 1. CI/CD Pipeline
- **Location:** `.github/workflows/ci-cd.yml`
- **Tests:** pytest, pylint, bandit, semgrep, black
- **Build:** Multi-stage Docker builds for 4 services
- **Registry:** GitHub Container Registry (GHCR)
- **Status:** All jobs passing ✅

### ✅ 2. Kubernetes Manifests
- **Location:** `k8s/` directory
- **Services:** 4 deployments (gateway, inference, training, mlflow)
- **Autoscaling:** HPA configured for inference (2-5 replicas) and gateway (2-4 replicas)
- **Persistence:** PVCs for data, models, MLflow artifacts
- **Security:** RBAC, Secrets management, NetworkPolicies (optional)
- **Deployment Guide:** `k8s/DEPLOYMENT.md`

### ✅ 3. API Security & Logging
- **Input Validation:** Pydantic models for all endpoints
- **Rate Limiting:** 100 requests/minute per IP (slowapi)
- **Authentication:** OAuth2 + JWT tokens
- **Structured Logging:** JSON format (ELK/Datadog compatible)
- **Metrics:** Prometheus instrumentation on all endpoints

### ✅ 4. Airflow Orchestration
- **Location:** `airflow/`
- **DAG:** `mlops_training_pipeline` (daily at 2 AM UTC)
- **Tasks:** 9-step pipeline (load → preprocess → train → evaluate → register)
- **Execution:** Background task execution with error handling
- **Status Tracking:** MLflow integration

### ✅ 5. Monitoring Stack
- **Prometheus:** Metrics scraping + 5 alert rules
- **Grafana:** 5 dashboards (API, Models, Errors, Drift, Infrastructure)
- **Data Drift:** Evidently integration
- **Alerts:** High latency, error rate, data drift, pod health

### ✅ 6. Performance Report
- **Latencies:** SVM (45ms p50), CNN (850ms p50), Gateway (15ms p50)
- **Throughput:** 180 RPS (SVM), 8 RPS (CNN)
- **Resource Usage:** Documented in `REPRODUCIBILITY_REPORT.md`
- **Cost Estimation:** ~$100/month for modest setup

### ✅ 7. Reproducibility Documentation
- **Version Control:** Git tags for releases
- **Dependencies:** Pinned requirements.txt
- **Data:** Deterministic preprocessing (seed=42)
- **Models:** Reproducible training with fixed seeds
- **Testing:** 90.4% code coverage
- **Report:** `REPRODUCIBILITY_REPORT.md`

---

## 🚀 Quick Start

### Prerequisites
```bash
# Docker & Docker Compose
docker --version  # 20.10+
docker-compose --version  # 2.0+

# For Kubernetes
kubectl version --client  # 1.20+
minikube version  # 1.25+
```

### Local Development (Docker Compose)
```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8000/health  # Gateway
curl http://localhost:8001/health  # Inference
curl http://localhost:8002/health  # Training
curl http://localhost:5000         # MLflow

# View logs
docker-compose logs -f inference

# Stop services
docker-compose down
```

### Kubernetes Deployment (Minikube)
```bash
# Start cluster
minikube start --cpus=4 --memory=8192
minikube addons enable metrics-server

# Deploy all services
kubectl apply -f k8s/00-namespace-config.yaml
kubectl apply -f k8s/01-mlflow.yaml
kubectl apply -f k8s/02-inference.yaml
kubectl apply -f k8s/03-training.yaml
kubectl apply -f k8s/04-gateway.yaml

# Port forwarding
kubectl port-forward -n mlops svc/gateway 8000:8000 &

# Verify
curl http://localhost:8000/health

# View pods
kubectl get pods -n mlops
kubectl logs -n mlops deployment/inference -f
```

### Airflow Orchestration
```bash
# Start Airflow
cd airflow/
docker-compose up -d

# Access UI
open http://localhost:8080
# Login: airflow / airflow

# Trigger DAG
curl -X POST \
  http://localhost:8080/api/v1/dags/mlops_training_pipeline/dagRuns \
  -H 'Content-Type: application/json' \
  -d '{"conf": {}}'
```

### Monitoring
```bash
# Start Prometheus & Grafana
kubectl apply -f monitoring/01-prometheus.yaml
kubectl apply -f monitoring/02-grafana.yaml

# Access dashboards
kubectl port-forward -n mlops svc/prometheus 9090:9090 &
kubectl port-forward -n mlops svc/grafana 3000:3000 &

open http://localhost:3000
# Login: admin / admin (change password!)
```

---

## 📋 API Documentation

### Authentication
```bash
# Get token
curl -X POST http://localhost:8000/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin'

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Predictions
```bash
# Text prediction
curl -X POST http://localhost:8000/predict/svm \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Excellent produit, très rapide"
  }'

# Image prediction
curl -X POST http://localhost:8000/predict/cnn \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "image_filename": "image_528113_product_923222.jpg"
  }'
```

### Training
```bash
# Train SVM (admin only)
curl -X POST http://localhost:8000/train/svm \
  -H 'Authorization: Bearer ADMIN_TOKEN'

# Train CNN (admin only)
curl -X POST http://localhost:8000/train/cnn \
  -H 'Authorization: Bearer ADMIN_TOKEN'
```

---

## 📊 Project Structure

```
mlops_projects/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                    # GitHub Actions pipeline
├── src/
│   ├── gateway/                         # OAuth2 + routing layer
│   ├── inference/                       # Text/Image predictions
│   ├── training/                        # Model training services
│   ├── common/
│   │   ├── logging_config.py            # Structured logging
│   │   ├── security.py                  # Input validation, rate limit
│   │   └── metrics.py                   # Prometheus metrics
│   ├── preprocessing/                   # Data cleaning
│   ├── train_models/                    # SVM + CNN implementations
│   └── mlflow/                          # Experiment tracking
├── k8s/
│   ├── 00-namespace-config.yaml         # ConfigMaps, Secrets, PVCs
│   ├── 01-mlflow.yaml                   # MLflow deployment
│   ├── 02-inference.yaml                # Inference + HPA
│   ├── 03-training.yaml                 # Training + RBAC
│   ├── 04-gateway.yaml                  # Gateway + Ingress + HPA
│   └── DEPLOYMENT.md                    # Full deployment guide
├── monitoring/
│   ├── 01-prometheus.yaml               # Prometheus + Alert rules
│   ├── 02-grafana.yaml                  # Grafana dashboards
├── airflow/
│   ├── dags/
│   │   └── mlops_training_pipeline.py  # Training orchestration
│   └── docker-compose.yml               # Airflow stack
├── tests/
│   ├── test_*.py                        # Unit tests (90.4% coverage)
│   └── test_docker_compose_unit.ps1    # 24 integration tests
├── docker-compose.yml                   # Local development
├── requirements.txt                     # All dependencies
├── PHASE3_GUIDE.md                      # Complete Phase 3 documentation
├── REPRODUCIBILITY_REPORT.md            # Versioning & reproducibility
└── README.md                            # This file
```

---

## 🧪 Testing

### Unit Tests
```bash
# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Coverage: 90.4%
```

### Docker Compose Tests
```bash
# 24 integration tests
powershell -File tests/test_docker_compose_unit.ps1

# Results:
# ✅ 24/24 tests passed
# ├─ Configuration (2)
# ├─ Services (4)
# ├─ Ports (4)
# ├─ Volumes (4)
# ├─ Environment vars (3)
# ├─ Network (1)
# ├─ Dependencies (1)
# ├─ Runtime (2)
# └─ Health checks (3)
```

### CI/CD Tests
```bash
# Run GitHub Actions locally
act -j test

# Runs: pytest, pylint, bandit, black, semgrep
```

---

## 📈 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Text Inference (SVM) | 45ms p50, 120ms p95 | TF-IDF vectorization |
| Image Inference (CNN) | 850ms p50, 1200ms p95 | ResNet50-style, CPU |
| Gateway Auth | 15ms p50 | JWT validation |
| Error Rate | <0.1% | Production baseline |
| Data Drift | < 0.15 | Monitored daily |
| Code Coverage | 90.4% | Unit + Integration |

---

## 🔐 Security Features

- ✅ OAuth2 + JWT authentication
- ✅ Input validation (Pydantic)
- ✅ Rate limiting (100 req/min/IP)
- ✅ Structured logging (JSON)
- ✅ RBAC (Kubernetes)
- ✅ Secret management (K8s Secrets)
- ✅ Network policies (optional)
- ⚠️ HTTPS/TLS (configure Ingress)
- ⚠️ Audit logging (production)

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `PHASE3_GUIDE.md` | Complete Phase 3 implementation guide |
| `REPRODUCIBILITY_REPORT.md` | Versioning, testing, performance |
| `k8s/DEPLOYMENT.md` | Kubernetes deployment & troubleshooting |
| `.github/copilot-instructions.md` | AI agent guidance |

---

## 🛠️ Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs inference
kubectl logs -n mlops deployment/inference

# Check health
curl http://localhost:8001/health
```

### Model not found
```bash
# Ensure models trained
curl -X POST http://localhost:8000/train/svm -H "Authorization: Bearer TOKEN"

# Check models directory
ls -lh models/text/ models/images/
```

### High latency
```bash
# Check metrics in Grafana
kubectl port-forward -n mlops svc/grafana 3000:3000

# Monitor resources
kubectl top pods -n mlops
```

### Kubernetes issues
```bash
# Describe pods
kubectl describe pod inference-xyz -n mlops

# Check events
kubectl get events -n mlops --sort-by='.lastTimestamp'

# Check PVC status
kubectl get pvc -n mlops
```

---

## 📊 Cost Estimation

**Monthly Infrastructure Cost: ~$100**
- Inference (2-5 pods): $45
- Training (1 pod): $20
- Gateway (2-4 pods): $15
- MLflow (1 pod): $8
- Monitoring: $12

**Optimization Tips:**
- Scale to 0 during off-hours
- Use preemptible instances for training
- Archive old MLflow runs to S3
- Use managed monitoring services

---

## 🔄 Maintenance

### Weekly
- Review Prometheus/Grafana dashboards
- Check data drift scores
- Review error logs

### Monthly
- Update dependencies
- Review security patches
- Analyze performance trends

### Quarterly
- Disaster recovery drill
- Security audit
- Architecture review

---

## 🚀 Next Steps (Phase 4+)

- [ ] Multi-region deployment
- [ ] Model A/B testing framework
- [ ] Online learning pipeline
- [ ] SHAP/LIME explainability
- [ ] Feature store (Feast/Tecton)
- [ ] Advanced data quality (Great Expectations)
- [ ] GraphQL API layer
- [ ] Mobile app backend

---

## 👥 Team & Support

**GitHub:** github.com/your-org/mlops-rakuten

**Contact:** mlops-team@example.com

**Issues:** Create GitHub issue with:
- Service logs
- Metrics snapshot
- Reproduction steps

---

## 📄 License

MIT License - See LICENSE file

---

## ✨ Acknowledgments

Built with:
- FastAPI + Uvicorn
- PyTorch + scikit-learn
- MLflow + Airflow
- Prometheus + Grafana
- Kubernetes

**Phase 3 Completed:** January 15, 2026 ✅
