# Métriques

from sklearn.metrics import classification_report, f1_score


def evaluate_model(y_true, y_pred):
    return {
        "f1_macro": f1_score(y_true, y_pred, average="macro"),
        "report": classification_report(y_true, y_pred)
    }