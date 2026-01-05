
#!/bin/bash
# Script de déploiement simplifié pour le projet MLOps Rakuten

# 1. Nettoyage des anciens conteneurs et volumes
echo "nettoyage conteneurs et volumes"
docker-compose down -v

# 2. Rebuild des images sans cache (pour éviter les artefacts)
echo " build des images de conteneurs avec de nouveaux artefacts"
docker-compose build --no-cache

# 3. Lancement des services en mode détaché (pour libérer le terminal)
echo "deploiement conteneurs sans log"
docker-compose up -d

# 4. Vérification que les services sont opérationnels
sleep 5 && docker-compose ps

# 5. Affiche les URLs des services (pour ton job dating)
echo " Micro Services déployés avec succès !"
echo "   - Gateway:    http://localhost:8000"
echo "   - Inference:  http://localhost:8001"
echo "   - MLflow:     http://localhost:5000"

# 6. Affiche les logs d'un service spécifique (ex: training)
# docker-compose logs -f training
# docker-compose logs -f inference
# docker-compose logs -f gateway