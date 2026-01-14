## Contexte et objectifs du projet
Ce projet vise à construire un modèle de classification automatique de descriptions textuelles de produits afin de prédire leur catégorie et ce afin d'aider le vendeur à mieux mettre en avant son produit.

L’objectif est de fournir:
    - une pipeline reproductible
    - un modèle évalué
    - une API d’inférence minimale prête à être déployée.

### Objectifs techniques

Construire un modèle robuste pour la classification de texte
Garantir la reproductibilité des résultats
Mettre à disposition une API d’inférence conteneurisée

### Objectifs MLOps

Séparer clairement data / features / modèles
Implémenter des tests unitaires
Fournir une traçabilité des données et des modèles
Déployer une API simple avec FastAPI + Docker


## Machine learning Canvas : besoins et coûts
![Aperçu](pics/image-1.png)


## KPIs (performance, coût et latence)

| KPI                    | Valeur            |
| -----------------------| ------------------|
| F1 macro               | Baseline ≥ 0.60   |
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


