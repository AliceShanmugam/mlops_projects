# Useful Commands Reference

Quick reference for common tasks in Phase 3.

## Docker & Docker Compose

```bash
# Start all services (local development)
docker-compose up -d

# View logs
docker-compose logs -f inference
docker-compose logs -f training
docker-compose logs -f gateway

# Stop services
docker-compose down

# Clean up
docker-compose down -v  # Remove volumes too

# Rebuild images
docker-compose build --no-cache

# Health check
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Kubernetes (Minikube)

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192
minikube addons enable metrics-server

# Deploy all services
kubectl apply -f k8s/00-namespace-config.yaml
kubectl apply -f k8s/01-mlflow.yaml
kubectl apply -f k8s/02-inference.yaml
kubectl apply -f k8s/03-training.yaml
kubectl apply -f k8s/04-gateway.yaml

# Check status
kubectl get pods -n mlops
kubectl get svc -n mlops
kubectl get hpa -n mlops

# View logs
kubectl logs -n mlops deployment/inference -f
kubectl logs -n mlops deployment/gateway -f
kubectl logs -n mlops deployment/training -f

# Port forwarding
kubectl port-forward -n mlops svc/gateway 8000:8000 &
kubectl port-forward -n mlops svc/inference 8001:8000 &
kubectl port-forward -n mlops svc/training 8002:8000 &
kubectl port-forward -n mlops svc/mlflow 5000:5000 &
kubectl port-forward -n mlops svc/prometheus 9090:9090 &
kubectl port-forward -n mlops svc/grafana 3000:3000 &

# Delete deployment
kubectl delete namespace mlops

# Scale manually
kubectl scale deployment inference -n mlops --replicas=5

# Update image
kubectl set image deployment/inference \
  inference=ghcr.io/user/mlops/inference:v2.0 -n mlops

# Rollback
kubectl rollout undo deployment/inference -n mlops
```

## Airflow

```bash
# Start Airflow
cd airflow/
docker-compose up -d

# Access UI
open http://localhost:8080

# View DAGs
docker exec airflow-scheduler airflow dags list

# Trigger DAG
docker exec airflow-scheduler \
  airflow dags trigger mlops_training_pipeline

# View task status
docker exec airflow-scheduler \
  airflow tasks list mlops_training_pipeline

# View logs
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
```

## GitHub Actions (Local Testing)

```bash
# Install act
brew install act

# Run workflow locally
act -j test
act -j build
act  # Run all jobs

# Run with specific file
act -f .github/workflows/ci-cd.yml
```

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test
pytest tests/test_api.py -v

# Run docker-compose unit tests
powershell -File tests/test_docker_compose_unit.ps1

# Load testing
ab -n 100 -c 5 http://localhost:8001/health
```

## Authentication & API

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d 'username=admin&password=admin' | jq -r '.access_token')

# Text prediction
curl -X POST http://localhost:8000/predict/svm \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Excellent product, very fast"}'

# Image prediction
curl -X POST http://localhost:8000/predict/cnn \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"image_filename": "image_528113_product_923222.jpg"}'

# Train SVM
curl -X POST http://localhost:8000/train/svm \
  -H "Authorization: Bearer $TOKEN"

# Train CNN
curl -X POST http://localhost:8000/train/cnn \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring

```bash
# Query Prometheus
curl http://localhost:9090/api/v1/query?query=mlops_requests_total

# View metrics endpoint
curl http://localhost:8001/metrics

# Grafana login
# Open: http://localhost:3000
# Login: admin / admin
```

## MLflow

```bash
# View experiments
mlflow experiments list

# View runs
mlflow runs list

# View model registry
curl http://localhost:5000/api/2.0/mlflow/registered-models/list

# View artifact
mlflow artifacts download -a models/text -u runs:/RUN_ID
```

## Git & Version Control

```bash
# View logs
git log --oneline

# Create tag
git tag -a v3.0.0 -m "Phase 3: Production ready"
git push origin v3.0.0

# List tags
git tag -l

# View current branch
git branch

# Switch branch
git checkout main
git checkout -b feature/new-feature
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Format code
black src/

# Lint code
pylint src/

# Security scan
bandit -r src/

# Type checking
mypy src/  # Optional
```

## Debugging

```bash
# Check pod details
kubectl describe pod -n mlops PODNAME

# Debug pod
kubectl exec -it -n mlops PODNAME -- /bin/bash

# Check events
kubectl get events -n mlops --sort-by='.lastTimestamp'

# Check PVC status
kubectl get pvc -n mlops
kubectl describe pvc -n mlops mlops-data

# Check resource usage
kubectl top pods -n mlops
kubectl top nodes

# Tail pod logs
kubectl logs -n mlops POD --tail=100 -f
kubectl logs -n mlops POD --previous  # Previous crashed pod
```

## Cleanup

```bash
# Clean Docker
docker system prune -a

# Clean Kubernetes
kubectl delete namespace mlops
minikube stop
minikube delete

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

## Performance Monitoring

```bash
# Memory profiling
pip install memory-profiler
python -m memory_profiler src/inference/main.py

# CPU profiling
pip install py-spy
py-spy record -o profile.svg -- python src/inference/main.py

# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8001/health

# Load testing with Apache JMeter
jmeter -n -t test_plan.jmx -l results.jtl
```

## Production Deployment

```bash
# Validate manifests
kubectl apply --dry-run=client -f k8s/

# Deploy monitoring first
kubectl apply -f monitoring/

# Deploy in order
kubectl apply -f k8s/00-namespace-config.yaml
kubectl apply -f k8s/01-mlflow.yaml
kubectl apply -f k8s/02-inference.yaml
kubectl apply -f k8s/03-training.yaml
kubectl apply -f k8s/04-gateway.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment/gateway -n mlops

# Check rollout status
kubectl rollout status deployment/gateway -n mlops -w

# Get external IP
kubectl get svc -n mlops
```

## Troubleshooting

```bash
# Check pod logs for errors
kubectl logs -n mlops deployment/inference | grep ERROR

# Check service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://inference:8000/health

# DNS resolution check
kubectl exec -it -n mlops PODNAME -- nslookup inference.mlops.svc.cluster.local

# Port forwarding test
telnet localhost 8001

# Check mount points
kubectl exec -it -n mlops PODNAME -- ls -la /app/models
```

## Data Management

```bash
# Copy file to pod
kubectl cp ./file -n mlops POD:/path/to/file

# Copy file from pod
kubectl cp POD:/path/to/file -n mlops ./file

# View PV content
kubectl exec -it -n mlops PODNAME -- ls -la /mnt/pvc/
```

## Useful Aliases (Add to ~/.bashrc)

```bash
alias k='kubectl'
alias kgp='kubectl get pods -n mlops'
alias kgs='kubectl get svc -n mlops'
alias kl='kubectl logs -n mlops -f'
alias kd='kubectl describe -n mlops'
alias kex='kubectl exec -it -n mlops'
alias kt='kubectl top pods -n mlops'
```

## Common Issues & Fixes

```bash
# Pod stuck in pending
kubectl describe pod POD -n mlops
# Usually: PVC not available or node capacity full

# High memory usage
kubectl set resources deployment DEPLOYMENT -n mlops \
  --limits=memory=2Gi --requests=memory=1Gi

# Pod crashes
kubectl logs POD -n mlops --previous

# Connection refused
kubectl port-forward -n mlops svc/inference 8001:8000

# Disk full
kubectl exec -it -n mlops POD -- df -h
# Clean old logs: kubectl delete pod -n mlops POD
```

---

**For more information, see PHASE3_GUIDE.md**
