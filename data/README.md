# ************************* FICHIER A MODIFIER *********************************************
# fichier à adapter !!!!!!

# Data Catalog — Rakuten MLOps Project

Ce dossier contient l’ensemble des données utilisées dans le projet MLOps basé sur le challenge Rakuten.

Les données sont organisées selon les bonnes pratiques MLOps afin de garantir :
- la traçabilité
- la reproductibilité
- l’absence de fuite de données
- la séparation claire des responsabilités (raw vs processed)

---

## 📦 Origine des données

- **Source** : Rakuten France – Challenge de classification produit
- **Plateforme** : https://challengedata.ens.fr
- **Type de données** :
  - Données textuelles (descriptions produits)
  - Données images (photos produits)
- **Tâche** : classification multi-classes de produits e-commerce

---

## 📁 Structure des données

data/
├── raw/
│ ├── X_train_update.csv
│ ├── Y_train_CVw08PX.csv
│ └── image_train/
│
├── raw_test/
│ ├── X_test_update.csv
│ └── image_test/
│
└── processed/

## 📂 `raw/` — Données brutes d’entraînement

### Fichiers

- **X_train_update.csv**
  - Contient les descriptions textuelles des produits
  - Colonnes principales :
    - `productid`
    - `designation`
    - `description`
    - `imageid`

- **Y_train_CVw08PX.csv**
  - Contient les labels associés aux produits
  - Colonnes principales :
    - `productid`
    - `prdtypecode` (classe cible)

- **image_train/**
  - Dossier contenant les images produits d’entraînement
  - Nommage des fichiers conforme au dataset Rakuten

### Règles d’usage

- ❌ Ces données ne doivent **jamais être modifiées**
- ❌ Aucun nettoyage ou transformation directe
- ✅ Utilisées uniquement en **lecture**
- ✅ Toute transformation doit être écrite dans `data/processed/`

---

## 📂 `raw_test/` — Données brutes de test / inférence

### Fichiers

- **X_test_update.csv**
  - Données textuelles de test (sans labels)
  - Même structure que `X_train_update.csv`

- **image_test/**
  - Images produits associées aux données de test

### Règles d’usage

- ❌ Aucune utilisation pour l’entraînement
- ✅ Utilisées pour :
  - l’inférence
  - l’évaluation finale
  - la démonstration API

---

## 📂 `processed/` — Données transformées

Ce dossier contiendra :
- données nettoyées
- features textuelles (TF-IDF, embeddings)
- features images (CNN)
- jeux de données prêts pour les modèles

⚠️ Les fichiers de ce dossier sont :
- générés automatiquement
- traçables
- versionnables si nécessaire

---

## 🔒 Gestion du versioning

- Les données brutes (`raw`, `raw_test`) **ne sont pas versionnées** dans Git
- Elles sont exclues via `.gitignore`
- Le code garantit leur traçabilité par :
  - tests automatisés
  - chemins standards
  - catalogage explicite

---

## 🧪 Tests associés

Des tests automatisés valident :
- l’existence des fichiers
- la séparation train / test
- la cohérence de la structure des données

Ces tests sont définis dans le dossier `tests/`.

---

## 📌 Notes MLOps

Ce catalogage permet :
- une intégration simple dans des pipelines automatisés
- une reproductibilité complète des expériences
- une maintenance facilitée du projet

Toute modification de structure doit être documentée dans ce fichier.