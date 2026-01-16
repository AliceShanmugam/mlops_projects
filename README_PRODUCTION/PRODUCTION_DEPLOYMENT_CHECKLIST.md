# Production Deployment Checklist

**Project:** MLOps Rakuten Classification Platform  
**Date:** January 15, 2026  
**Phase:** 3 (Production Ready)

---

## Pre-Deployment (1 Week Before)

### Infrastructure Preparation
- [ ] Cloud infrastructure provisioned (AWS/GCP/Azure)
- [ ] Kubernetes cluster created (1.20+)
- [ ] Node scaling policies configured
- [ ] Persistent storage provisioned
- [ ] Network policies defined
- [ ] Load balancer configured
- [ ] DNS records updated

### Security Setup
- [ ] SSL/TLS certificates provisioned (Let's Encrypt)
- [ ] Secrets management (HashiCorp Vault / AWS Secrets Manager)
- [ ] RBAC roles created
- [ ] Service accounts configured
- [ ] Network security groups/NACLs updated
- [ ] Image scanning configured (Trivy/Snyk)
- [ ] Container registry access configured
- [ ] API rate limiting configured

### Monitoring Setup
- [ ] Prometheus storage provisioned (SSD)
- [ ] Grafana deployed and secured
- [ ] Alert routing configured (Slack/PagerDuty)
- [ ] Log aggregation setup (ELK/Datadog)
- [ ] APM configured (optional: Jaeger/Datadog)
- [ ] Backup alerting configured

### Database Preparation
- [ ] PostgreSQL for Airflow (managed service)
- [ ] MLflow backend database (managed service)
- [ ] Database backups configured
- [ ] Connection pooling configured
- [ ] Performance tuning completed

---

## Deployment Day (T-Day)

### 1. Pre-Flight Checks (T - 2 hours)
- [ ] All CI/CD tests passing
- [ ] Docker images pushed to registry
- [ ] Kubernetes manifests validated: `kubectl apply --dry-run=client -f k8s/`
- [ ] Secrets created in production namespace
- [ ] ConfigMaps updated with production values
- [ ] DNS propagation verified
- [ ] Backup of production cluster taken
- [ ] Incident response team on standby

### 2. Phase 1: Deploy Monitoring (T - 1h 30m)
```bash
# Deploy monitoring first to track deployment
kubectl apply -f monitoring/01-prometheus.yaml
kubectl apply -f monitoring/02-grafana.yaml

# Verify
kubectl wait --for=condition=available --timeout=300s \
  deployment/prometheus -n mlops
kubectl wait --for=condition=available --timeout=300s \
  deployment/grafana -n mlops

# Check dashboards accessible
kubectl port-forward -n mlops svc/grafana 3000:3000
# Open http://localhost:3000 and login
```
- [ ] Prometheus scraping targets healthy
- [ ] Grafana dashboards loading
- [ ] Alerts firing correctly

### 3. Phase 2: Deploy Data Layer (T - 1 hour)
```bash
# Create namespace and config
kubectl apply -f k8s/00-namespace-config.yaml

# Deploy MLflow
kubectl apply -f k8s/01-mlflow.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment/mlflow -n mlops
```
- [ ] MLflow pod running
- [ ] MLflow database connection working
- [ ] Persistent volume mounted
- [ ] MLflow UI accessible

### 4. Phase 3: Deploy Services (T - 45 min)
```bash
# Deploy in order: inference → training → gateway
kubectl apply -f k8s/02-inference.yaml
kubectl wait --for=condition=available --timeout=300s \
  deployment/inference -n mlops

kubectl apply -f k8s/03-training.yaml
kubectl wait --for=condition=available --timeout=300s \
  deployment/training -n mlops

kubectl apply -f k8s/04-gateway.yaml
kubectl wait --for=condition=available --timeout=300s \
  deployment/gateway -n mlops
```
- [ ] Inference pod(s) running (2 replicas minimum)
- [ ] Training pod running
- [ ] Gateway pod(s) running (2 replicas minimum)
- [ ] All health checks passing
- [ ] PVC mounted correctly

### 5. Phase 4: Validation (T - 15 min)
```bash
# Port forward and test
kubectl port-forward -n mlops svc/gateway 8000:8000 &
kubectl port-forward -n mlops svc/prometheus 9090:9090 &
kubectl port-forward -n mlops svc/grafana 3000:3000 &

# Health checks
curl -v http://localhost:8000/health
curl -v http://localhost:8001/health  (via service)
curl -v http://localhost:8002/health  (via service)

# Authentication
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d 'username=admin&password=PROD_PASSWORD' | jq -r '.access_token')

# Test predictions
curl -X POST http://localhost:8000/predict/svm \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test product description"}'
```
- [ ] All health endpoints return 200 OK
- [ ] Authentication working
- [ ] Predictions returning valid responses
- [ ] Response times acceptable
- [ ] No errors in logs
- [ ] Metrics visible in Prometheus
- [ ] Grafana dashboards populating

### 6. Phase 5: Load Testing (T - 5 min)
```bash
# Light load test (don't overwhelm)
ab -n 100 -c 5 http://localhost:8000/health

# Monitor in Grafana
# Check: request rates, latencies, errors
```
- [ ] Load distributed across replicas
- [ ] No unusual error rates
- [ ] Latencies within SLA
- [ ] HPA not triggering unexpectedly

### 7. Go Live (T + 0)
```bash
# Switch DNS/LB to new deployment
# Update load balancer configuration
# Gradual traffic shift if possible (canary deployment)

# Monitor closely
kubectl logs -n mlops -f deployment/gateway
kubectl logs -n mlops -f deployment/inference
```
- [ ] Traffic flowing to new cluster
- [ ] Error rate < 0.1%
- [ ] All metrics green in Grafana
- [ ] No customer complaints

---

## Post-Deployment (T + 24 hours)

### Verification
- [ ] All pods in running state
- [ ] No restarts/crashes in logs
- [ ] PVC usage growing as expected (not full)
- [ ] Database connections healthy
- [ ] Backups completed successfully
- [ ] Alerts firing correctly (test one)
- [ ] Monitoring retention adequate
- [ ] API response times stable

### Performance Analysis
- [ ] P50, P95, P99 latencies measured
- [ ] Throughput baseline established
- [ ] Resource utilization reasonable
- [ ] No memory leaks (stable over 24h)
- [ ] CPU usage even across replicas
- [ ] Network bandwidth acceptable

### Security Verification
- [ ] TLS certificates valid
- [ ] Rate limiting working (test: 101st request)
- [ ] Authentication enforced
- [ ] No sensitive data in logs
- [ ] Secrets not exposed
- [ ] RBAC policies enforced
- [ ] Network policies blocking correctly

### Data Science Validation
- [ ] Models loaded correctly
- [ ] Predictions match training metrics
- [ ] No data drift detected initially
- [ ] MLflow experiments logged
- [ ] Model accuracy acceptable (>85%)

---

## Post-Deployment (T + 1 week)

### Stability Checks
- [ ] Zero unplanned restarts
- [ ] Error rate < 0.1% sustained
- [ ] Data drift monitoring running
- [ ] Alerts accurate (no alert fatigue)
- [ ] On-call team never paged
- [ ] Backup restore tested

### Performance Optimization
- [ ] Identify optimization opportunities
- [ ] Profile CPU/memory usage
- [ ] Review slow queries (if applicable)
- [ ] Optimize resource requests
- [ ] Review cost vs performance tradeoff

### Documentation Updates
- [ ] Runbook created for common issues
- [ ] Postmortem documented (if any incidents)
- [ ] Architecture diagram updated
- [ ] Team trained on new platform
- [ ] Disaster recovery procedures tested

---

## Rollback Plan

### Immediate Rollback (If Critical Issue)
```bash
# Delete new deployment and restore old
kubectl delete deployment -n mlops gateway inference training
kubectl apply -f k8s/OLD_WORKING_VERSION/

# Or use GitOps (Flux/ArgoCD)
git revert <commit>
git push origin main
# ArgoCD auto-syncs to previous version
```

- [ ] Previous version images still in registry
- [ ] Previous ConfigMaps/Secrets available
- [ ] Database rollback procedure tested
- [ ] Communication plan for outage

### Gradual Rollback
```bash
# Use canary deployment (50% old, 50% new)
kubectl scale deployment gateway --replicas=2 -n mlops  # old
kubectl scale deployment gateway-new --replicas=2 -n mlops  # new

# Monitor metrics
# If all good: scale old to 0
# If problems: scale new to 0 and revert
```

---

## Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| DevOps Lead | | | @devops-oncall |
| Platform Lead | | | @platform-oncall |
| Data Science | | | @ds-oncall |
| SRE Manager | | | @sre-manager |

---

## Success Criteria

✅ **Deployment Successful If:**
- All pods running and healthy
- All endpoints responding (latency < 500ms)
- Error rate < 0.1%
- No data loss
- Alerts functioning
- Team confident in system
- No customer impact

⚠️ **Potential Issues:**
- If: Pod stuck in pending → Check PVC/node capacity
- If: High latency → Check load, scaling, CPU throttling
- If: Database connection errors → Check credentials, network
- If: OOM errors → Increase memory limits
- If: Disk full → Clean old logs/artifacts

---

## Post-Go-Live Monitoring (First Week)

### Daily Checks
```bash
# View pod status
kubectl get pods -n mlops

# Check metrics
kubectl port-forward -n mlops svc/prometheus 9090:9090
# Open http://localhost:9090 and review graphs

# View recent logs
kubectl logs -n mlops -l app=inference --tail=100 -f
```

### Weekly Review
- [ ] Capacity planning (is scaling adequate?)
- [ ] Cost analysis (unexpected charges?)
- [ ] Model performance (still accurate?)
- [ ] User feedback (any complaints?)
- [ ] Security incidents (any breaches?)
- [ ] On-call effectiveness (response times?)

---

## Compliance & Sign-Off

### Pre-Deployment Approval
- [ ] Security team approval: _____________ Date: _____
- [ ] DevOps lead approval: ______________ Date: _____
- [ ] Data science lead approval: ________ Date: _____
- [ ] Product manager approval: ________ Date: _____

### Post-Deployment Sign-Off
- [ ] Deployment completed successfully: _____ Time: _____
- [ ] All checks passed: __________________ Date: _____
- [ ] Team confident in system: __________ Date: _____
- [ ] Handoff to operations: ____________ Date: _____

---

## Notes & Lessons Learned

**What went well:**
```
[ ] Add items
```

**What could improve:**
```
[ ] Add items
```

**Action items for next deployment:**
```
[ ] Add items
```

---

**Document Prepared By:** _______________  
**Date:** January 15, 2026  
**Version:** 1.0  

**For questions:** Contact mlops-team@example.com
