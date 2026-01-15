import pandas as pd
from bs4 import BeautifulSoup
import html
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from deep_translator import GoogleTranslator
from tqdm import tqdm
import os

# Charger les données
df_products = pd.read_excel("data/X_train_update.xlsx") # Contient designation, description, productID, imageID
df_labels = pd.read_excel("data/Y_train_CVw08PX.xlsx")  # Contient prdtypecode

# Fusionner les deux dataframes sur l'index
df_concat = pd.concat([df_products, df_labels], axis=1)
df = df_concat[['designation', 'description', 'productid', 'imageid','prdtypecode']]

df.loc[:, 'description'] = df['description'].fillna('')

# Regrouper colonnes designations et descriptions
df["text"] = df["designation"].astype(str).fillna('') + " " + df["description"].astype(str).fillna('')

# nettoyer cette nouvelle colonne
df['text'] = df['text'].apply(lambda x: BeautifulSoup(html.unescape(x), "html.parser").get_text(separator=" ", strip=True))
df['text'] = df['text'].apply(lambda x : x.lower())

df_jeux_videos = df[df['prdtypecode'].isin([40,60,50])]
df_jeux_videos['label'] = 0

df_livres = df[df['prdtypecode'].isin([10, 2705])]
df_livres['label']=1

df_jeux_societe = df[df['prdtypecode'].isin([1160, 1281])]
df_jeux_societe['label']=2

df_maquettes_drones = df[df['prdtypecode']==1300]
df_maquettes_drones['label']=3

df_mobilier = df[df['prdtypecode']==1560]
df_mobilier['label']=4

df_deco_maison = df[df['prdtypecode']==2060]
df_deco_maison['label']=5

df_fourniture = df[df['prdtypecode']==2522]
df_fourniture['label']=6

df_jardin_piscine = df[df['prdtypecode'].isin([2582, 2585])]
df_jardin_piscine['label']=7

df_labeled = pd.concat([df_jeux_videos,df_livres, df_jeux_societe, df_maquettes_drones, df_mobilier, df_deco_maison, df_fourniture, df_jardin_piscine]).reset_index()
df_labeled.drop(columns='index', inplace=True)

df_labeled.loc[:, 'description'] = df_labeled['description'].fillna('')
df_labeled["text"] = df_labeled["designation"].astype(str).fillna('') + " " + df_labeled["description"].astype(str).fillna('')

df_labeled['text'] = df_labeled['text'].apply(lambda x: BeautifulSoup(html.unescape(x), "html.parser").get_text(separator=" ", strip=True))
df_labeled['text'] = df_labeled['text'].apply(lambda x : x.lower())

# Pour des résultats plus stables
DetectorFactory.seed = 0

# Fonction de détection avec gestion des erreurs
def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

# Ajouter une nouvelle colonne 'langue'
df_labeled['langue'] = df_labeled['text'].apply(detect_language)

# Traduire uniquement les descriptions non-françaises
def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='fr').translate(text)
    except Exception:
        return text  # en cas d'erreur, retourne le texte original

# Créer colonne 'description_fr', identique à l'original
df_labeled['text_fr'] = df_labeled['text']

# Traduire uniquement si langue ≠ 'fr' et texte non vide
mask_non_fr = (df_labeled['langue'] != 'fr') & (df_labeled['langue'] != 'unknown') & (df_labeled['text'].str.strip() != "")

# Appliquer traduction avec barre de progression
tqdm.pandas(desc="Traduction en français") 
df_labeled.loc[mask_non_fr, 'text_fr'] = df_labeled.loc[mask_non_fr, 'text'].progress_apply(translate_text)

### A utiliser pour ne pas run la commande au dessus chronophage?
df_labeled.to_csv('data/processed/df_labeled_fr.csv', index=False)


### Ajouter la vectorisation tfidf dedans