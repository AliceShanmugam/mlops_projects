# Tests API avec cURL - MLOps Rakuten

Guide complet pour tester les endpoints d'inférence et de training avec cURL.

## Configuration des services

Assurez-vous que les services sont en cours d'exécution :
```powershell
docker-compose up -d
```

**Ports disponibles** :
- Gateway: `http://localhost:8000`
- Inference: `http://localhost:8001`
- Training: `http://localhost:8002`
- MLflow: `http://localhost:5000`

---

## 1. TESTS D'AUTHENTIFICATION (Gateway)

### 1.1 Obtenir un token d'authentification (Admin)
```powershell
$response = curl.exe -X POST "http://localhost:8000/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
  
$response
```

**Réponse attendue** :
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 1.2 Obtenir un token utilisateur standard
```powershell
curl.exe -X POST "http://localhost:8000/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=user&password=user123"
```

---

## 2. TESTS DE SANTÉ (Health Check)

### 2.1 Vérifier la santé du Gateway
```powershell
curl.exe -X GET "http://localhost:8000/health"
```

### 2.2 Vérifier la santé du service Inference
```powershell
curl.exe -X GET "http://localhost:8001/health"
```

### 2.3 Vérifier la santé du service Training
```powershell
curl.exe -X GET "http://localhost:8002/health"
```

---

## 3. TESTS D'INFÉRENCE (Prédictions)

### 3.1 Prédiction par TEXTE uniquement
```powershell
$token = "YOUR_BEARER_TOKEN"

curl.exe -X POST "http://localhost:8000/predict/text" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Chaussures de sport Nike Air Max confortables pour la course"
  }'
```

**Réponse attendue** :
```json
{
  "prediction": "Chaussures",
  "confidence": 0.92,
  "category_id": 2
}
```

### 3.2 Prédiction par IMAGE uniquement
```powershell
$token = "YOUR_BEARER_TOKEN"

curl.exe -X POST "http://localhost:8000/predict/image" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "image_name": "image_528113_product_923222.jpg"
  }'
```

### 3.3 Prédiction MULTIMODALE (Texte + Image)
```powershell
$token = "YOUR_BEARER_TOKEN"

curl.exe -X POST "http://localhost:8000/predict" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Chaussures de sport Nike Air Max confortables",
    "image_name": "image_528113_product_923222.jpg"
  }'
```

**Réponse attendue** :
```json
{
  "text_prediction": {
    "category": "Chaussures",
    "confidence": 0.92
  },
  "image_prediction": {
    "category": "Chaussures",
    "confidence": 0.88
  },
  "ensemble_prediction": "Chaussures",
  "ensemble_confidence": 0.90
}
```

**Logique d'ensemble** :
- Si texte et image s'accordent → moyenne des confiances
- Si texte et image divergent → prédiction du modèle le plus confiant
- Si un seul modèle disponible → sa prédiction utilisée directement

### 3.4 Prédiction par batch (plusieurs produits)
```powershell
$token = "YOUR_BEARER_TOKEN"

curl.exe -X POST "http://localhost:8000/predict/batch" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "items": [
      {"text": "T-shirt coton blanc", "image_name": "image_001.jpg"},
      {"text": "Jeans bleu slim fit", "image_name": "image_002.jpg"},
      {"text": "Chemise formelle rouge", "image_name": "image_003.jpg"}
    ]
  }'
```

---

## 4. TESTS DE TRAINING (Entraînement de modèles)

### 4.1 Entraîner le modèle SVM (Texte)
```powershell
$adminToken = "YOUR_ADMIN_TOKEN"

curl.exe -X POST "http://localhost:8000/train/svm" `
  -H "Authorization: Bearer $adminToken" `
  -H "Content-Type: application/json" `
  -d '{
    "run_name": "svm_training_v1",
    "test_size": 0.2,
    "random_state": 42
  }'
```

**Réponse attendue** :
```json
{
  "status": "training_started",
  "task_id": "task_12345",
  "message": "Entraînement SVM lancé en arrière-plan",
  "mlflow_run_id": "abc123def456"
}
```

### 4.2 Entraîner le modèle CNN (Images)
```powershell
$adminToken = "YOUR_ADMIN_TOKEN"

curl.exe -X POST "http://localhost:8000/train/cnn" `
  -H "Authorization: Bearer $adminToken" `
  -H "Content-Type: application/json" `
  -d '{
    "run_name": "cnn_training_v1",
    "epochs": 20,
    "batch_size": 32,
    "learning_rate": 0.001,
    "test_size": 0.2
  }'
```

### 4.3 Récupérer le statut d'entraînement
```powershell
$adminToken = "YOUR_ADMIN_TOKEN"
$taskId = "task_12345"

curl.exe -X GET "http://localhost:8000/train/status/$taskId" `
  -H "Authorization: Bearer $adminToken"
```

**Réponse attendue** :
```json
{
  "task_id": "task_12345",
  "status": "completed",
  "progress": 100,
  "metrics": {
    "accuracy": 0.85,
    "precision": 0.87,
    "recall": 0.83,
    "f1_score": 0.85
  },
  "training_time": 1234.56
}
```

### 4.4 Entraîner les deux modèles (SVM + CNN) en parallèle
```powershell
$adminToken = "YOUR_ADMIN_TOKEN"

# Lancer SVM
curl.exe -X POST "http://localhost:8000/train/svm" `
  -H "Authorization: Bearer $adminToken" `
  -H "Content-Type: application/json" `
  -d '{"run_name": "svm_v2"}'

# Lancer CNN en parallèle
curl.exe -X POST "http://localhost:8000/train/cnn" `
  -H "Authorization: Bearer $adminToken" `
  -H "Content-Type: application/json" `
  -d '{"run_name": "cnn_v2", "epochs": 15}'
```

---

## 5. TESTS DIRECTS AUX SERVICES (bypass Gateway)

### 5.1 Inférence directe sur le service Inference (port 8001)
```powershell
curl.exe -X POST "http://localhost:8001/predict/text" `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Montre digitale sportive avec GPS"
  }'
```

### 5.2 Training direct sur le service Training (port 8002)
```powershell
curl.exe -X POST "http://localhost:8002/train/svm" `
  -H "Content-Type: application/json" `
  -d '{
    "run_name": "direct_svm_test"
  }'
```

---

## 6. MONITORING & METRICS

### 6.1 Récupérer les métriques Prometheus du Gateway
```powershell
curl.exe -X GET "http://localhost:8000/metrics"
```

### 6.2 Lister tous les runs MLflow
```powershell
curl.exe -X GET "http://localhost:5000/api/2.0/mlflow/experiments/list"
```

### 6.3 Détails d'un run MLflow spécifique
```powershell
$runId = "abc123def456"

curl.exe -X GET "http://localhost:5000/api/2.0/mlflow/runs/get?run_id=$runId"
```

---

## 7. COMMANDES UTILES PowerShell

### 7.1 Sauvegarder un token dans une variable
```powershell
# Récupérer et parser le token
$loginResponse = curl.exe -X POST "http://localhost:8000/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123" | ConvertFrom-Json

$token = $loginResponse.access_token
Write-Host "Token obtenu: $token"
```

### 7.2 Tester rapidement tous les health checks
```powershell
Write-Host "=== Gateway Health ===" 
curl.exe http://localhost:8000/health

Write-Host "`n=== Inference Health ===" 
curl.exe http://localhost:8001/health

Write-Host "`n=== Training Health ===" 
curl.exe http://localhost:8002/health

Write-Host "`n=== MLflow Health ===" 
curl.exe http://localhost:5000/health
```

### 7.3 Script de test complet
```powershell
# Authentification
Write-Host "1. Authentification..."
$loginResp = curl.exe -s -X POST "http://localhost:8000/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123" | ConvertFrom-Json
$token = $loginResp.access_token

# Test inférence
Write-Host "2. Test inférence texte..."
curl.exe -X POST "http://localhost:8000/predict/text" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"text": "Cet article est magnifique"}'

# Test training
Write-Host "3. Lancement training SVM..."
curl.exe -X POST "http://localhost:8000/train/svm" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"run_name": "quick_test"}'

Write-Host "`nTests terminés!"
```

---

## 8. EXEMPLES AVEC FICHIERS

### 8.1 Télécharger une image pour inférence
```powershell
# Copier une image du dossier data dans le conteneur
docker cp data/raw/image_train/image_528113_product_923222.jpg inference_AF:/app/data/

# Utiliser l'image pour l'inférence
$token = "YOUR_TOKEN"
curl.exe -X POST "http://localhost:8000/predict/image" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"image_name": "image_528113_product_923222.jpg"}'
```

---

## 9. DÉPANNAGE

### Erreur 401 (Unauthorized)
```powershell
# Générer un nouveau token
curl.exe -X POST "http://localhost:8000/token" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
```

### Erreur 503 (Service Unavailable)
```powershell
# Vérifier les logs du service
docker-compose logs inference
docker-compose logs training
```

### Erreur de connexion
```powershell
# Vérifier que les services sont en cours d'exécution
docker-compose ps

# Redémarrer les services
docker-compose restart
```

---

## 10. FICHIER .env (Optionnel)

Créez un fichier `test_config.ps1` pour automatiser les tests :

```powershell
# test_config.ps1
$GATEWAY_URL = "http://localhost:8000"
$INFERENCE_URL = "http://localhost:8001"
$TRAINING_URL = "http://localhost:8002"
$MLFLOW_URL = "http://localhost:5000"

$ADMIN_USER = "admin"
$ADMIN_PASS = "admin123"

# Fonction helper
function Get-AuthToken {
    param($user, $pass)
    $response = curl.exe -s -X POST "$GATEWAY_URL/token" `
      -H "Content-Type: application/x-www-form-urlencoded" `
      -d "username=$user&password=$pass" | ConvertFrom-Json
    return $response.access_token
}

$TOKEN = Get-AuthToken $ADMIN_USER $ADMIN_PASS
Write-Host "Token obtenu: $TOKEN"
```

Puis lancez-le :
```powershell
. .\test_config.ps1
```

---

## Notes

- Remplacez `YOUR_BEARER_TOKEN` par le token obtenu via le endpoint `/token`
- Les noms d'images doivent correspondre aux fichiers dans `data/raw/image_train/`
- Les textes doivent être en français ou anglais selon vos données d'entraînement
- Adaptez les paramètres (epochs, batch_size, test_size) selon vos besoins
