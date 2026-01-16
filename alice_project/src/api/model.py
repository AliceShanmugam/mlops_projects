import joblib
import numpy as np

MODEL_PATH = "models/model.joblib"

model = joblib.load(MODEL_PATH)

def predict(features: list[float]):
    X = np.array(features).reshape(1, -1)
    prediction = model.predict(X)
    return prediction[0]