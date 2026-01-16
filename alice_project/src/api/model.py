import joblib

MODEL_PATH = "models/test_pipeline.joblib"

pipeline = joblib.load(MODEL_PATH)

def predict(text: str):
    return pipeline.predict([text])[0]