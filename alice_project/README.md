## Contexte et objectifs du projet
Ce projet vise à construire un modèle de classification automatique de descriptions textuelles de produits afin de prédire leur catégorie et ce afin d'aider le vendeur à mieux mettre en avant son produit.

L’objectif est de fournir:  
    - une pipeline reproductible  
    - un modèle évalué  
    - une API d’inférence minimale prête à être déployée.  

### Objectifs techniques

Construire un modèle robuste pour la classification de texte.   
Garantir la reproductibilité des résultats.  
Mettre à disposition une API d’inférence conteneurisée.  

### Objectifs MLOps

Séparer clairement data / features / modèles.  
Implémenter des tests unitaires.  
Fournir une traçabilité des données et des modèles.  
Déployer une API simple avec FastAPI + Docker.  


## Machine learning Canvas : besoins et coûts
![Aperçu](pics/image-1.png)


## KPIs (performance, coût et latence)

| KPI                    | Valeur            |
| -----------------------| ------------------|
| F1 macro               | Baseline ≥ 0.70   |
| Latence inférence      | < 50 ms           |
| Taille modèle          | SVM < 50 MB       |
| Couverture vocabulaire | TF-IDF 2k         |  


## Architecture du projet

### Architecture globale
```
[Raw Data]
    ↓
[Preprocessing]
    ↓
[TF-IDF Vectorization]
    ↓
[Model Training (Logistic Regression / SVM / XGBoost)]
    ↓
[Evaluation & Selection]
    ↓
[Model Artifact]
    ↓
[FastAPI]
    ↓
[Client]
```

### Workflow
```
Notebook (EDA / baseline)
        ↓
Python scripts (train, test)
        ↓
Docker build
        ↓
API d’inférence
```

### Structure du projet 
```
ml-project/
│
├── data/
│   ├── raw/                    # données brutes
│   ├── processed/              # données nettoyées
│   └── data_quality_report.md
│
├── notebooks/
│   └── baseline_model.ipynb
│
├── src/
│   ├── preprocessing.py        # nettoyage texte
│   ├── model.py                # pipelines ML
│   ├── evaluate.py             # métriques
│   └── train.py                # script d’entraînement
│
├── api/
│   └── main.py                 # API FastAPI
│
├── tests/
│   ├── test_data.py
│   ├── test_features.py
│   └── test_predictions.py
│
├── models/
│   └── model.pkl
│
├── Dockerfile
├── Makefile
├── requirements.txt
└── README.md

```


## Traitement des données

Le traitement des données consiste à :  
    - la collecte des données > recupérées directement depuis le site Rakuten Challenge ( descritpions, titres et labels)  
    - le nettoyage des données > afin de les utiliser pour nos modèles par la suite (passage en minuscules, suppression des caractères spéciaux, encodage des labels, etc.)

⚠️ Les données utilisées pour la classification ont été filtrées à partir des données initiales pour les répartir dans 8 catégories différentes.


## Modèles de machine learning

Les descriptions produits sont transformées en représentations numériques à l’aide de TFIDF, puis classifiées via un modèle SVM.

⚠️ Dans le cadre de ce projet nous allons nous focaliser sur les descriptions en francais et procéder à une traduction en français lors du preprocessing.


## Tests unitaires

Les tests garantissent la stabilité des données, des features et des prédictions avant déploiement.


## API d'inférence

On utilise FastAPI.
Un chargement du modèle préentraîné est attendu lorsqu'un call API est effectué pour réaliser une inférence en temps réel.


## Commandes docker
⚠️ Se placer dans le dossier alice-project :  

Pour build l'image
(deprecate, use docker compose)
> docker build -t rakuten-ml-challenge . (bash)

Les gros fichiers (Excel, datasets, modèles) ne sont pas copiés dans l’image.  
On ajoute seulement les fichiers raws via volumes Docker au moment du run car les scripts qui tourneront dans le conteneur vont générer automatiquement les fichiers processed et le modèle :
(deprecate, use docker compose)
> sudo docker run --rm -v ./data:/app/data -v ./models:/app/models rakuten-ml-challenge (bash)

Ou utiliser avec le Makefile:  
(deprecate, use docker compose)
> make build
> make run

Ou utiliser docker-compose:  
> docker compose up --build (pour construire l'image) à utiliser si on modifie le dockerfile aussi
> docker compose up (si on modifie les scripts mais pas le docker compose)

> docker compose up mlflow
> docker compose up preprocessing
> docker compose up training
> docker compose up api

Pour arreter le conteneur: 
> docker compose down

Lancer le docker en mode interactif
(deprecate, use docker compose)
> docker run -it \
  -v $(PWD)/data:/app/data \
  -v $(PWD)/models:/app/models \
  rakuten-ml-challenge \
  /bin/bash

Build api  
> docker build -f Dockerfile.api -t rakuten-api .

Run api  (apres ouverture nouvelle session)
etape 0:
> docker rm rakuten-api-container 
Pour supprimer l'ancien conteneur ayant le meme nom

etape 1: (deprecate, use docker compose)
> docker images (liste toutes les images)
> docker ps -a (liste tous les conteneurs eteints et allumés)
> docker run -d --name rakuten-api-container -p 8000:8000 -v ./models:/app/models rakuten-api

etape 3:
api
> http://localhost:8000/docs

mlflow
> http://localhost:5000
