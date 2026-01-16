# MLOps Phase 3: Complete Production Deployment Guide

## Overview
Phase 3 finalizes the MLOps platform with:
1. **CI/CD Pipeline** (GitHub Actions)
2. **Orchestration** (Airflow DAGs)
3. **Kubernetes Deployment** (K8s manifests + HPA)
4. **Monitoring & Observability** (Prometheus + Grafana)
5. **Security** (Input validation, Auth, Rate limiting, Logging)

---

## Part 1: CI/CD Pipeline

### GitHub Actions Workflow
Location: `.github/workflows/ci-cd.yml`

**Jobs:**
1. **Tests & Code Quality**
   - Run pytest with coverage
   - Pylint linting
   - Bandit security scan
   - Black code formatting
   - Semgrep SAST analysis

2. **Build & Push Docker Images**
   - Build for gateway, inference, training, mlflow
   - Push to GHCR (GitHub Container Registry)
   - Cache layers for speed

3. **Integration Tests**
   - Validate docker-compose.yml
   - Start services & health checks
   - Run docker-compose unit tests

4. **Artifacts**
   - Generate SBOM (Software Bill of Materials)
   - Upload test results

**Running Locally:**
```bash
# Install act (run GitHub Actions locally)
brew install act

# Run workflow
act -j test
```

---

## Part 2: Security Enhancements

### API Security Implementation

**Files Created:**
- `src/common/logging_config.py` - Structured JSON logging
- `src/common/security.py` - Input validation, rate limiting
- `src/common/metrics.py` - Prometheus metrics

### Features

**1. Structured Logging**
```python
from src.common.logging_config import setup_logging
logger = setup_logging("inference")
logger.info("Request processed", extra={"request_id": "123", "duration_ms": 45})
# Output: JSON format suitable for ELK/Datadog
```

**2. Input Validation (Pydantic)**
```python
from src.common.security import PredictTextRequest
request = PredictTextRequest(text="my product")  # Validated
```

**3. Rate Limiting**
- 100 requests per minute per IP
- Returns 429 Too Many Requests

**4. Metrics Collection**
- Request counts, latencies
- Model prediction metrics
- Error tracking
- Data drift monitoring

### Integration Example
```python
# src/inference/main.py
from fastapi import FastAPI
from src.common.security import limiter, PredictTextRequest
from prometheus_client import make_asgi_app

app = FastAPI()
app.state.limiter = limiter

@app.post("/predict/svm")
@limiter.limit("100/minute")
async def predict_svm(request: PredictTextRequest):
    # Validated input, rate limited, logged
    pass

# Add metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

## Part 3: Kubernetes Deployment

### Files
- `k8s/00-namespace-config.yaml` - Namespace, ConfigMap, Secrets, PVCs
- `k8s/01-mlflow.yaml` - MLflow deployment
- `k8s/02-inference.yaml` - Inference service + HPA
- `k8s/03-training.yaml` - Training service + RBAC
- `k8s/04-gateway.yaml` - Gateway + Ingress + HPA
- `k8s/DEPLOYMENT.md` - Full deployment guide

### Quick Start (Minikube)
```bash
# Start cluster
minikube start --cpus=4 --memory=8192
minikube addons enable metrics-server

# Deploy (order matters!)
kubectl apply -f k8s/00-namespace-config.yaml
kubectl apply -f k8s/01-mlflow.yaml
kubectl apply -f k8s/02-inference.yaml
kubectl apply -f k8s/03-training.yaml
kubectl apply -f k8s/04-gateway.yaml

# Port forwarding
kubectl port-forward -n mlops svc/gateway 8000:8000 &

# Verify
curl http://localhost:8000/health
```

### Autoscaling
```bash
# View HPA status
kubectl get hpa -n mlops

# Manual scale
kubectl scale deployment inference -n mlops --replicas=5

# Watch autoscaling
kubectl get hpa -n mlops -w
```

### Updates
```bash
# Rolling update
kubectl set image deployment/inference \
  inference=ghcr.io/your-org/inference:v2.0 -n mlops

# Rollback
kubectl rollout undo deployment/inference -n mlops
```

---

## Part 4: Airflow Orchestration

### DAG: mlops_training_pipeline
Location: `airflow/dags/mlops_training_pipeline.py`

**Schedule:** Daily at 2 AM UTC
**Duration:** ~30-60 minutes

### Tasks
1. **Validation** - Verify dependencies
2. **Data Loading** - Load raw CSV
3. **Preprocessing** - Clean & validate
4. **Feature Engineering** - TF-IDF, vectorization
5. **Data Splitting** - Train/Val/Test (70/15/15)
6. **Model Training** - SVM + CNN (parallel)
7. **Evaluation** - Compute metrics
8. **Registration** - Register to MLflow
9. **Completion** - Notify via Slack/Email

### Running Airflow
```bash
# Start Airflow stack
cd airflow/
docker-compose up -d

# Access UI
open http://localhost:8080
# Login: airflow / airflow

# Set variables
# Settings → Admin → Variables
# Add: api_token = "your-jwt-token"

# Trigger DAG
# Trigger DAG from UI or:
docker exec airflow-scheduler \
  airflow dags trigger mlops_training_pipeline
```

---

## Part 5: Monitoring & Observability

### Prometheus
Location: `monitoring/01-prometheus.yaml`

**Metrics Scraped:**
- Gateway (10s interval)
- Inference (10s interval)
- Training (30s interval)
- MLflow (30s interval)
- Kubernetes pods

**Alerts Configured:**
- High inference latency (p95 > 1.0s)
- High error rate (> 5%)
- Data drift detected (score > 0.3)
- Pod not running
- PV almost full (> 85%)

### Grafana
Location: `monitoring/02-grafana.yaml`

**Dashboards:**
- API Request Rates
- Model Latencies (p50, p95, p99)
- Error Rates by Type
- Data Drift Scores
- Infrastructure Health

**Access:**
```bash
kubectl port-forward -n mlops svc/grafana 3000:3000
open http://localhost:3000
# Login: admin / admin (change password!)
```

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `mlops_request_duration_seconds` | API latency | p95 > 1.0s |
| `mlops_model_prediction_duration_seconds` | Model inference time | > 500ms |
| `mlops_errors_total` | Error count | rate > 5% |
| `mlops_data_drift_score` | Data drift (0-1) | > 0.3 |
| `mlops_model_accuracy` | Model accuracy | < 0.85 |

---

## Part 6: Testing & Validation

### Unit Tests
```bash
pytest tests/ -v --cov=src
```

### Docker Compose Tests
```bash
powershell -File tests/test_docker_compose_unit.ps1
# All 24 tests covering config, ports, volumes, env vars, health checks
```

### Integration Tests (CI/CD)
- Docker image building
- docker-compose validation
- Health checks (all services)
- Endpoint tests

---

## Part 7: Performance & Profiling

### Load Testing
```bash
# Install Apache Bench
brew install httpd

# Test inference latency
ab -n 1000 -c 10 http://localhost:8001/health

# With authentication
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" \
  http://localhost:8001/predict/svm
```

### Memory Profiling
```bash
# Add to inference service
pip install memory-profiler
python -m memory_profiler src/inference/main.py
```

### CPU Profiling
```bash
pip install py-spy
py-spy record -o profile.svg -- python src/inference/main.py
```

---

## Part 8: Reproducibility & Versioning

### Model Versioning
```bash
# MLflow automatically versions models
# Access from MLflow UI

# Query models via API
curl http://localhost:5000/api/2.0/mlflow/registered-models/list
```

### Data Versioning (DVC)
```bash
# Optional: DVC for data versioning
pip install dvc
dvc add data/raw/X_train_update.csv
git add data/raw/X_train_update.csv.dvc
git commit -m "Track training data v1.0"
```

### Environment Reproducibility
```bash
# Freeze requirements
pip freeze > requirements-prod.txt

# Dockerfile uses requirements.txt
# All services built with consistent deps
```

---

## Part 9: Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Enable RBAC in Kubernetes
- [ ] Configure network policies
- [ ] Set up Secret encryption at rest
- [ ] Enable audit logging
- [ ] Configure image scanning (Trivy, Snyk)

### Performance
- [ ] Run load tests (k6, Locust)
- [ ] Monitor CPU/Memory under load
- [ ] Optimize model inference (quantization, pruning)
- [ ] Cache predictions when possible
- [ ] Use CDN for static assets

### Reliability
- [ ] Set up multi-region failover
- [ ] Configure PV backups
- [ ] Test disaster recovery
- [ ] Set up service monitoring
- [ ] Document runbooks

### Compliance
- [ ] GDPR data retention policies
- [ ] Model fairness audits
- [ ] Data access logs
- [ ] Regular security audits
- [ ] Documentation of decisions

---

## Part 10: Cost Optimization

### Infrastructure Costs
| Component | Resource | Cost Reduction |
|-----------|----------|---|
| Inference | Pod replicas | Use HPA (scale to 0 off-hours) |
| Training | Spot instances | Use preemptible VMs |
| Storage | PVCs | Archive old models to S3 |
| Monitoring | Prometheus | Use managed Datadog/New Relic |

### Example: Cloud Cost Estimation
```
Inference (2-5 pods, 512MB RAM, 250m CPU):
  ~$50/month (AWS EKS nano)

Training (1 pod, 2GB RAM, 2 CPU):
  ~$30/month

MLflow (1 pod, 512MB RAM, 100m CPU):
  ~$20/month

Monitoring (Prometheus + Grafana):
  ~$15/month

Total (modest setup):
  ~$115/month
```

---

## Troubleshooting

### Common Issues

**1. Pod not starting**
```bash
kubectl describe pod inference-xyz -n mlops
kubectl logs inference-xyz -n mlops
```

**2. PVC pending**
```bash
kubectl get pvc -n mlops
kubectl describe pvc mlops-data -n mlops
# May need to create PV first
```

**3. Service unavailable**
```bash
# Check service endpoints
kubectl get endpoints -n mlops
# Check DNS resolution
kubectl exec -it pod/debug -n mlops -- nslookup inference
```

**4. High latency**
```bash
# Check metrics in Grafana
# View pod resource usage
kubectl top pods -n mlops
# Check node capacity
kubectl top nodes
```

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [FastAPI Security](https://fastapi.tiangolo.com/advanced/security/)

---

## Support & Maintenance

### Weekly Tasks
- [ ] Review monitoring dashboards
- [ ] Check data drift scores
- [ ] Review error logs
- [ ] Verify backup integrity

### Monthly Tasks
- [ ] Update dependencies
- [ ] Review security patches
- [ ] Analyze model performance trends
- [ ] Capacity planning review

### Quarterly Tasks
- [ ] Disaster recovery drill
- [ ] Security audit
- [ ] Cost optimization review
- [ ] Architecture review

---

**Last Updated:** January 2026
**Phase 3 Status:** Complete
**Production Ready:** Yes
