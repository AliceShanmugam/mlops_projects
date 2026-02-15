import os
import joblib
import mlflow
import mlflow.sklearn
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score, classification_report
from sklearn.pipeline import Pipeline

mlflow.set_experiment("text_classification")

# Création de dossier models s'il n'existe pas
os.makedirs("models", exist_ok=True)

X_train = joblib.load("data/processed/X_train_tfidf.joblib")
y_train = joblib.load("data/processed/y_train.joblib")
X_test = joblib.load("data/processed/X_test_tfidf.joblib")
y_test = joblib.load("data/processed/y_test.joblib")

with mlflow.start_run():

    # Paramètres
    mlflow.log_param("model_type", "LinearSVC")
    mlflow.log_param("random_state", 42)
    mlflow.log_param("threshold", 0.6)

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

    # Log métrique
    mlflow.log_metric("f1_macro", f1)

    # Condition de sauvegarde
    THRESHOLD = 0.6

    if f1 >= THRESHOLD:
        joblib.dump(model, "models/svm.joblib")
        mlflow.log_artifact("models/svm.joblib")
        print(f"✅ Modèle sauvegardé (F1 ≥ {THRESHOLD})")
    else:
        print(f"❌ Modèle NON sauvegardé (F1 < {THRESHOLD})")
        print("👉 Essayez de changer de modèle, d'hyperparamètres ou de features.")

    # Création de pipeline complète pour la production
    tfidf_vectorizer = joblib.load("models/tfidf_vectorizer.joblib")
    pipeline = Pipeline([
        ("tfidf", tfidf_vectorizer),
        ("svm", model)
    ])

    joblib.dump(pipeline, "models/text_pipeline.joblib")

    # Log modèle complet
    mlflow.sklearn.log_model(pipeline, "model")

    # Log rapport texte
    with open("classification_report.txt", "w") as f:
        f.write(classification_report(y_test, y_pred))

    mlflow.log_artifact("classification_report.txt")