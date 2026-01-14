import pandas as pd
from bs4 import BeautifulSoup
import html

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