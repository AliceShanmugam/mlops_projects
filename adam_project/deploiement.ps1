# deploiement.ps1
Write-Host "1. Nettoyage des anciens conteneurs et volumes..."
docker-compose down -v

Write-Host""
Write-Host "2. Rebuild des images sans cache..."
docker-compose build --no-cache

Write-Host""
Write-Host "3. Lancement des services sans logs (-d)"
docker-compose up -d

Write-Host""
Write-Host"4. Affichage des services lancés"
docker-compose ps

Write-Host""
Write-Host "5. Services deployes avec succes !"
Write-Host "   - Gateway:    http://localhost:8000"
Write-Host "   - Inference:  http://localhost:8001"
Write-Host "   - MLflow:     http://localhost:5000"

# Affiche les logs d'un service spécifique (ex: training)
Write-Host""
Write-Host "6. logs de services specifiques"
docker-compose logs -f training
docker-compose logs -f inference
# docker-compose logs -f gateway
# docker-compose logs -f mlflow