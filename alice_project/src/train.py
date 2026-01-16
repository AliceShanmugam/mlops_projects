import os
import joblib
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score, classification_report

# Création de dossier models s'il n'existe pas
os.makedirs("models", exist_ok=True)

X_train = joblib.load("data/processed/X_train_tfidf.joblib")
y_train = joblib.load("data/processed/y_train.joblib")
X_test = joblib.load("data/processed/X_test_tfidf.joblib")
y_test = joblib.load("data/processed/y_test.joblib")

# Entraînement
model = LinearSVC(random_state=42)
model.fit(X_train, y_train)

# Prédictions
y_pred = model.predict(X_test)

# Évaluation
f1 = f1_score(y_test, y_pred, average="macro")

print("===== ÉVALUATION =====")
print(classification_report(y_test, y_pred))
print(f"F1-score macro : {f1:.3f}")

# Condition de sauvegarde
THRESHOLD = 0.6

if f1 >= THRESHOLD:
    joblib.dump(model, "models/svm.joblib")
    print(f"✅ Modèle sauvegardé (F1 ≥ {THRESHOLD})")
else:
    print(f"❌ Modèle NON sauvegardé (F1 < {THRESHOLD})")
    print("👉 Essayez de changer de modèle, d'hyperparamètres ou de features.")