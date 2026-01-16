### Projet MLOps - Challenge RAKUTEN - Déploiement de modéles de classification multimodale

# Objectifs du projet

Le projet vise à créer une architecture MLOps réaliste permettant :
de deployer La classification automatique de produits à partir :
  du texte (SVM + TF-IDF)
  des images (CNN from scratch)
La reproductibilité complète des entraînements et inférences
La traçabilité et le suivi des données, modèles et métriques
Une API d’inférence conteneurisée et sécurisée
Une architecture microservices prête pour l’industrialisation
l'orchestation de pipeline complet et scalable

# Structure du repository

mlops_projects/
├── api/ # API FastAPI
├── data/
│ ├── raw/ # Données brutes d’entraînement
│ ├── raw_test/ # Données brutes de test
│ ├── processed/ # Données prétraitées
│ └── README.md # Data catalog
├── mlflow/ # tracking et suivi MLFLow
│ └──  mlruns/ # artefacts de MLFlow
├── models/ # modeles entraînés svm & cnn
│ ├── images/ # modeles entrainés cnn
│ └── text/ # modeles entrainiés tfidf + svm
├── services/ # microservices conteneurisés
│ ├── gateway/ # service authentification
│ ├── inference/ # service prédiction
│ ├── training/ # service entrainement de modéles
├── src/
│ ├── preprocessing/ # Nettoyage texte et images
│ ├── features/ # TF-IDF
│ ├── models/ # modeles SVM et CNN
│ ├── pipelines/ # Entraînement modeles SVM et CNN
├── tests/ # Tests unitaires
├── requirements.txt # framework à installer 
├── pytest.ini # test uniquement mlops_projects/tests
├── Makefile
├── docker-compose.yml #conteneurisation des microservices
├── deploiement.ps1 # build et deploiement conteneurs
└── README.md

# Phase 1 Fondations & Conteneurisation

## les KPI (performance, coût, latence)

| Catégorie          | KPI                                       |
| ------------------ | ----------------------------------------- |
| Performance modèle | Accuracy / F1-macro                       |
| Robustesse         | Tests unitaires (data, features, API)     |
| Reproductibilité   | Docker + scripts d’entraînement           |
| Latence API        | < 3 s (en locale)                      |
| Traçabilité        | MLflow (params, metrics, artefacts)       |
| monitoring         | suivi des données et des metriques        |
| Scalabilité        | Séparation training / inference / gateway |

## Données et traitement
data/
├── raw/
│   ├── X_train.csv
│   ├── y_train.csv
│   └── image_train/
├── raw_test/
│   └── image_test/
└── processed/
    └── train_clean.csv

Nettoyage du texte : src/preprocessing/text_cleaning.py
Construction des features TF-IDF : src/features/build_features.py
Gestion des valeurs manquantes, Normalisation & tokenisation, Traçabilité des transformations

## Modèles & entraînement
models/
├── text/
│   ├── svm.joblib
│   └── tfidf.joblib
└── images/
    └── cnn.pt

Modèle texte 
TF-IDF + Linear SVM
Script : src/models/train_linearsvm.py
Pipeline : src/pipelines/run_training_text.py

Modèle image
CNN from scratch (PyTorch)
Script : src/models/train_cnn.py
Pipeline : src/pipelines/run_training_images.py

## Tests unitaires
Localisés dans tests/ :
test_read_data.py → chargement des données
test_preprocessing.py → nettoyage texte
test_features.py → TF-IDF
test_model_training2.py → entraînement modèles
test_api.py → endpoints FastAPI
lancement des tests (validation des données, modèles, pretraitement, API)
  bash : pytest

## API d’inférence
localisé dans api/main.py
Endpoints
GET /health	      ==> Healthcheck
POST /predict/svm	==> Prédiction texte
POST /predict/cnn	==> Prédiction image

lancement de l'API en local
  bash : python -m api.main

# Phase 2 Microservices

## ML Flow et suivi d'experience
mlflow/
├── Dockerfile
├── mlflow.db
└── mlruns/
ML Flow conteneurisé

## Services
services/gateway : authentification ==> FastAPI + OAuth2 (admin / user) + accès aux services (inference, training, mlflow)
services/infernces : prediction ==> Chargement des modèles entraînés + Prédiction texte & image
services/training : entrainement ==> Entraînement SVM & CNN + Enregistrement des modèles

Architecture microservices
[ Client ]
    |
    v
[ Gateway sécurisé ]
    |
    +--> [ Inference ]
    |
    +--> [ Training ]
    |
    +--> [ MLflow ]

## Orchestration Docker Compose
Services exposés :
  Gateway, Port:8000
  inference, Port:8002
  training, Port:8001
  MLflow UI, Port:5000

integration docker compose : nettoyage, rebuild images et lancement des services
bash : ./deploiement.ps1

tests unitaires d'integration docker-compose
bash : ./tests/test_docker-compose.ps1

token
curl -X 'POST' \
  'http://127.0.0.1:8000/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=admin&password=admin123'

predict/svm
  curl -X 'POST' \
  'http://127.0.0.1:8000/predict/svm' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2ODU2NzQ5OH0.NfuqpCW0SPFs6Lgn659sGcM_57EcEWegkDwJis6SPHg' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Ordinateur portable 15 pouces, 8GB RAM, SSD 256GB"
}'

predict/cnn
curl -X 'POST' \
  'http://127.0.0.1:8000/predict/cnn' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2ODU2NzQ5OH0.NfuqpCW0SPFs6Lgn659sGcM_57EcEWegkDwJis6SPHg' \
  -H 'Content-Type: application/json' \
  -d '{
  "image_path": "data/raw/image_train/image_528113_product_923222.jpg"
}'