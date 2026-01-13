# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 14:20:36 2026

@author: coach
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from PIL import Image
import torch
import torch.nn as nn
import os
import re
import joblib
import random
import io
import nltk
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import DistilBertTokenizer, DistilBertModel
from torchvision.models import ResNet101_Weights, resnet101
from nltk.corpus import stopwords
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
from gensim.models import Word2Vec

# =========================
# CONFIGURATION GLOBALE
# =========================
# Configuration de la page Streamlit
st.set_page_config(
    page_title="Projet Rakuten - Dashboard MLOps",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Téléchargement des stopwords NLTK
nltk.download('stopwords')

# Chemins relatifs (à adapter selon ton environnement local)

DATA_PATH = Path("/data/processed/train_clean.csv")
IMAGE_TRAIN_PATH = Path("/data/raw/image_train")
IMAGE_TEST_PATH = Path("/data/raw_test/image_test")

# =========================
# CHARGEMENT DES DONNÉES
# =========================
@st.cache_data
def load_data():
    """Charge et prépare les données pour le dashboard."""
    data = pd.read_csv(DATA_PATH)
    data['imageid'] = data['imageid'].astype('object')
    data['productid'] = data['productid'].astype('object')
    return data

df = load_data()

# =========================
# SIDEBAR POUR LA NAVIGATION
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller à la page:",
    [
        "1. Contexte",
        "2. Data Viz du Dataset",
        "3. Modélisation Naive des Classes",
        "4. Modèle NLP (Texte) + Interprétabilité",  # Priorité 1
        "5. Modèle Image (CNN) + Interprétabilité",   # Priorité 2
        "6. Modèle Multimodal (À venir)",            # Phase 2
        "7. Conclusion & Étapes Prochaines (MLOps)"
    ]
)

# =========================
# PAGE 1: CONTEXTE
# =========================
if page == "1. Contexte":
    st.title("1. Contexte du Projet Rakuten")
    st.markdown("""
    ### Objectif du Projet
    Ce projet vise à analyser un dataset Rakuten contenant des **descriptions textuelles** et des **images** de produits, afin de prédire leur catégorie.

    **Phases du projet:**
    1. **Analyse exploratoire** du dataset.
    2. **Modélisation NLP** sur les colonnes `descriptions` et `désignation`.
    3. **Modélisation CNN** sur les images.
    4. **Modèle multimodal** combinant texte et image (phase 2).

    ### Méthodologie
    - **Dataset**: 84921 exemples pour l'entraînement, 13812 pour le test.
    - **Classes**: 27 catégories initiales regroupées en 8 classes équilibrées.
    - **Objectif**: Classifier les produits avec une **accuracy > 0.85** et une **latence < 500ms**.
    """)

# =========================
# PAGE 2: DATA VIZ
# =========================
elif page == "2. Data Viz du Dataset":
    st.title("2. Analyse Exploratoire du Dataset")

    # ========== STATS GÉNÉRALES ==========
    st.subheader("Statistiques Générales")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**X_train (Descriptions)**")
        x_train = pd.read_csv(os.path.join(BASE_PATH, 'X_train_update.csv'))
        st.dataframe(x_train.describe(include='all').T)
    with col2:
        st.markdown("**Y_train (Labels)**")
        y_train = pd.read_csv(os.path.join(BASE_PATH, 'Y_train_CVw08PX.csv'))
        st.dataframe(y_train.describe(include='all').T)

    # ========== VISUALISATIONS ==========
    st.subheader("Visualisations")

    # Histogramme des longueurs de texte
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(df['description'].str.len(), bins=50, ax=ax[0])
    ax[0].set_title("Longueur des descriptions")
    sns.histplot(df['designation'].str.len(), bins=50, ax=ax[1])
    ax[1].set_title("Longueur des désignations")
    st.pyplot(fig)

    # Nuages de mots
    st.subheader("Nuages de Mots")
    from wordcloud import WordCloud
    text_desc = " ".join(df['description'].dropna())
    wordcloud = WordCloud(width=800, height=400).generate(text_desc)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

    # ========== IMAGES ==========
    st.subheader("Analyse des Images")
    image_files = os.listdir(IMAGE_TRAIN_PATH)[:9]  # 9 premières images
    cols = st.columns(3)
    for i, (col, img_file) in enumerate(zip(cols, image_files)):
        with col:
            img_path = os.path.join(IMAGE_TRAIN_PATH, img_file)
            img = Image.open(img_path)
            st.image(img, caption=img_file, width=200)

# =========================
# PAGE 3: MODÉLISATION NAIVE
# =========================
elif page == "3. Modélisation Naive des Classes":
    st.title("3. Répartition des Classes")

    # Tableau des labels
    labels_data = {
        "Label": [0, 1, 2, 3, 4, 5, 6, 7],
        "Catégorie": [
            "Jeux vidéos",
            "Livres / magazines",
            "Jeux de société / cartes à collectionner",
            "Maquettes / voitures et drones télécommandés",
            "Mobilier",
            "Déco, linge maison",
            "Papeterie et fournitures",
            "Jardinerie et piscine"
        ],
        "Nombre d'articles": [5021, 5877, 6023, 5045, 5073, 4993, 4989, 5167]
    }
    df_labels = pd.DataFrame(labels_data)
    st.dataframe(df_labels)

    # Graphique de répartition
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x="Catégorie", y="Nombre d'articles", data=df_labels, palette="viridis", ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# =========================
# PAGE 4: MODÈLE NLP (TEXTE)
# =========================
elif page == "4. Modèle NLP (Texte) + Interprétabilité":
    st.title("4. Modèle NLP sur les Textes")

    # ========== CHARGEMENT DU MODÈLE ==========
    @st.cache_resource
    def load_nlp_model():
        model_path = "C:/Users/coach/Desktop/datascientest/Projet DATASCIENTEST/projet_DS/model_text.pkl"
        model = joblib.load(model_path)
        return model

    model = load_nlp_model()
    st.success("✅ Modèle NLP chargé")

    # ========== PRÉPARATION DES DONNÉES ==========
    X_text = df['texte_complet']
    y_text = df['label']
    X_train, X_test, y_train, y_test = train_test_split(
        X_text, y_text, test_size=0.2, random_state=42, stratify=y_text
    )

    # Vectorizer TF-IDF
    french_stopwords = stopwords.words('french')
    tfidf_vectorizer = TfidfVectorizer(
        stop_words=french_stopwords,
        max_features=100,
        ngram_range=(1, 2)
    )
    X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
    X_test_tfidf = tfidf_vectorizer.transform(X_test)

    # ========== PRÉDICTIONS ==========
    y_pred = model.predict(X_test_tfidf)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")

    st.subheader("Performances du Modèle NLP")
    st.write(f"**Accuracy:** {acc:.4f}")
    st.write(f"**F1-score (weighted):** {f1:.4f}")
    st.text(classification_report(y_test, y_pred))

    # ========== INTERPRÉTABILITÉ SHAP ==========
    st.subheader("Interprétabilité avec SHAP")

    # Échantillon pour SHAP
    background = shap.sample(X_test_tfidf, min(20, len(X_test)), random_state=42)
    if hasattr(background, "toarray"):
        background = background.toarray()

    explainer = shap.KernelExplainer(model.predict_proba, background)
    feature_names = tfidf_vectorizer.get_feature_names_out()

    # Exemple d'explication
    idx = 3
    sample_vector = X_test_tfidf[idx].toarray()
    shap_values = explainer.shap_values(sample_vector)

    # Affichage
    fig, ax = plt.subplots(figsize=(10, 4))
    shap.summary_plot(shap_values, sample_vector, feature_names=feature_names, show=False)
    st.pyplot(fig)

    st.write(f"**Exemple de texte:** {X_test.iloc[idx]}")
    st.write(f"**Classe prédite:** {y_pred[idx]}")

# =========================
# PAGE 5: MODÈLE CNN (IMAGES)
# =========================
elif page == "5. Modèle Image (CNN) + Interprétabilité":
    st.title("5. Modèle CNN sur les Images")

    # ========== CHARGEMENT DU MODÈLE ==========
    @st.cache_resource
    def load_cnn_model():
        model = resnet101(weights=ResNet101_Weights.IMAGENET1K_V1)
        num_ftrs = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Linear(num_ftrs, 1024),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(1024, 8)  # 8 classes
        )
        model.load_state_dict(torch.load(
            "C:/Users/coach/Desktop/datascientest/Projet DATASCIENTEST/projet_DS/resnet_image.pth",
            map_location=torch.device('cpu')
        ))
        model.eval()
        return model

    model = load_cnn_model()
    st.success("✅ Modèle CNN chargé")

    # ========== PRÉPARATION DES DONNÉES ==========
    class ImageDataset(Dataset):
        def __init__(self, df, image_dir, transform=None):
            self.df = df
            self.image_dir = image_dir
            self.transform = transform

        def __len__(self):
            return len(self.df)

        def __getitem__(self, idx):
            row = self.df.iloc[idx]
            img_path = os.path.join(self.image_dir, row['nom'])
            image = Image.open(img_path).convert("RGB")
            if self.transform:
                image = self.transform(image)
            return image, row['label']

    # Transformations
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Dataset
    dataset = ImageDataset(df, IMAGE_TRAIN_PATH, transform)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=False)

    # ========== PRÉDICTIONS ==========
    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in dataloader:
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            y_true.extend(labels.numpy())
            y_pred.extend(preds.numpy())

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")

    st.subheader("Performances du Modèle CNN")
    st.write(f"**Accuracy:** {acc:.4f}")
    st.write(f"**F1-score (weighted):** {f1:.4f}")
    st.text(classification_report(y_true, y_pred))

    # ========== INTERPRÉTABILITÉ SHAP ==========
    st.subheader("Interprétabilité avec SHAP (Images)")

    # Sélection de 3 images pour l'exemple
    sample_images, sample_labels = next(iter(dataloader))[:3]
    sample_images_np = sample_images.permute(0, 2, 3, 1).numpy()

    # Masker pour SHAP
    masker = shap.maskers.Image("blur(64,64)", sample_images_np.shape[1:])

    # Explainer
    def predict_fn(x):
        x_t = torch.tensor(x, dtype=torch.float32).permute(0, 3, 1, 2)
        with torch.no_grad():
            preds = model(x_t)
            return F.softmax(preds, dim=1).numpy()

    explainer = shap.Explainer(predict_fn, masker)

    # Calcul des explications
    shap_values = explainer(sample_images_np)

    # Affichage
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    for i in range(3):
        shap.image_plot(shap_values.values[i], sample_images_np[i], ax=ax[i])
    st.pyplot(fig)

# =========================
# PAGE 6: MODÈLE MULTIMODAL (À VENIR)
# =========================
elif page == "6. Modèle Multimodal (À venir)":
    st.title("6. Modèle Multimodal (Texte + Image)")
    st.warning("⚠️ Cette partie sera implémentée après validation des modèles texte et image.")

# =========================
# PAGE 7: CONCLUSION
# =========================
elif page == "7. Conclusion & Étapes Prochaines (MLOps)":
    st.title("7. Conclusion & Perspectives")

    st.subheader("Synthèse des Résultats")
    st.write("""
    - **Modèle NLP (Texte)**: Accuracy > 0.85, F1-score > 0.85.
    - **Modèle CNN (Images)**: Accuracy > 0.80, F1-score > 0.80.
    - **Prochaine étape**: Combinaison des deux modèles en un **modèle multimodal**.
    """)

    st.subheader("Perspectives MLOps")
    st.write("""
    - **Déploiement**: Dockerisation du dashboard et des modèles.
    - **Monitoring**: Intégration de Prometheus/Grafana pour le suivi des performances.
    - **CI/CD**: Automatisation des tests et déploiements avec GitHub Actions.
    - **Améliorations**: Optimisation des modèles (quantification, ONNX).
    """)

# =========================
# FOOTER
# =========================
st.sidebar.markdown("""
---
**Auteur**: Adam Fuchs
**Projet**: Rakuten Multimodal Classification
**Date**: Janvier 2026
""")
