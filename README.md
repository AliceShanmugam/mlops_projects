# Rakuten Product Classification multimodal — MLOps Project

## 🎯 Objectif du projet

L’objectif de ce projet est de concevoir un **MVP MLOps complet** pour la
classification automatique de produits e-commerce Rakuten à partir de
données textuelles (et à terme images).

Le projet met l’accent sur :
- la reproductibilité des expérimentations
- la traçabilité des données et des modèles
- l’industrialisation du modèle via une API d’inférence

### Phase 1

## 📊 KPIs (Indicateurs clés)

Les indicateurs suivis pour évaluer le système sont :

- **Performance modèle**
  - F1-score macro (classification multi-classes)
- **Latence**
  - Temps de réponse de l’API d’inférence
- **Robustesse**
  - Tests unitaires (données, features, modèle)
- **Reproductibilité**
  - Versioning des artefacts (TF-IDF, SVM)
  - Environnement contrôlé via dépendances

---

## 🧱 Architecture du projet
dev (local)
├── data ingestion & preprocessing
├── feature engineering (TF-IDF)
├── model training (SVM)
└── tests unitaires
↓
build
├── artefacts versionnés (tfidf.joblib, svm.joblib)
└── validation des performances
↓
run
└── API FastAPI d’inférence

## 📁 Structure du repository

mlops_projects/
├── api/ # API FastAPI
├── data/
│ ├── raw/ # Données brutes d’entraînement
│ ├── raw_test/ # Données brutes de test
│ ├── processed/ # Données prétraitées
│ └── README.md # Data catalog
├── src/
│ ├── preprocessing/ # Nettoyage texte
│ ├── features/ # TF-IDF
│ ├── models/ # Entraînement SVM
├── tests/ # Tests unitaires
├── models/ # Artefacts entraînés
├── requirements.txt
├── pytest.ini #test uniquement mlops_projects/src
└── README.md


---

## 📦 Données

Les données utilisées proviennent du **challenge Rakuten France**.

- Données textuelles : descriptions produits
- Données images : photos produits (non utilisées dans le baseline)

Les règles de gestion des données sont :
- les données brutes (`data/raw`, `data/raw_test`) sont **immutables**
- les transformations sont écrites dans `data/processed`
- les données ne sont pas versionnées dans Git (via `.gitignore`)

👉 Voir le **data catalog détaillé** : `data/README.md`

---

## 🧹 Prétraitement des données

Le prétraitement est implémenté dans :
src/preprocessing/text_cleaning.py

Étapes principales :
- concaténation `designation` + `description`
- suppression HTML
- normalisation (minuscules, caractères spéciaux)
- mapping des labels Rakuten vers des classes numériques
- détection de langue

---

## 🧠 Modèle baseline

Le modèle baseline repose sur :

- **Vectorisation** : TF-IDF
- **Classifieur** : SVM linéaire (`SVC(kernel="linear")`)

Le pipeline respecte les bonnes pratiques MLOps :
- TF-IDF entraîné uniquement sur le jeu d’apprentissage
- séparation stricte train / validation
- artefacts versionnés (`tfidf.joblib`, `svm.joblib`)

Les métriques calculées incluent :
- F1-score macro
- rapport de classification par classe

---

## 🧪 Tests unitaires

Des tests automatisés valident :
- l’existence et la structure des données
- le prétraitement texte
- la construction des features TF-IDF
- l’entraînement et l’évaluation du modèle
- l’API d’inférence

Lancement des tests :

```bash
pytest

## API d’inférence

Une API FastAPI minimale permet de réaliser des prédictions à partir de descriptions produits.

### Lancement local
```bash
uvicorn api.main:app --reload

### Phase 2

