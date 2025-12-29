# flows/ml_flow.py
from prefect import flow, task
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import mlflow
import mlflow.sklearn
import os


# Task to generate a synthetic classification dataset and split it.
@task(name="Generate Data")
def generate_data():
    # Create synthetic data with 1000 samples and 20 features
    X, y = make_classification(n_samples=1000, n_features=20, n_classes=2)
    # Split the data: 80% training, 20% testing
    return train_test_split(X, y, test_size=0.2)


# Task to train a Logistic Regression model.
@task(name="Train Model")
def train_model(X_train, y_train):
    model = LogisticRegression()
    model.fit(X_train, y_train)
    return model


# Task to evaluate the model's accuracy.
@task(name="Evaluate Model")
def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)


# Main Prefect flow that wraps the entire process.
@flow(name="ML Training Flow with MLflow")
def train_and_evaluate():
    # Step 1: Set the MLflow tracking URI from the environment variable.
    # If the environment variable is not set, 
    # it will default to "http://localhost:5001"
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    print("MLflow Tracking URI:", mlflow.get_tracking_uri())

    # Step 2: Start an MLflow run so that everything within 
    # this block is tracked.
    with mlflow.start_run() as run:
        # Generate and split data.
        X_train, X_test, y_train, y_test = generate_data()

        # Log a parameter about data splitting.
        mlflow.log_param("test_size", 0.2)

        # Step 3: Train the model.
        model = train_model(X_train, y_train)

        # Step 4: Log the trained model as an artifact and register 
        # it in the MLflow Model Registry.
        # The 'registered_model_name' parameter will register the model 
        # under that name.
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name="LogisticRegressionModel"
        )

        # Step 5: Evaluate the model and log the accuracy metric.
        accuracy = evaluate_model(model, X_test, y_test)
        mlflow.log_metric("accuracy", accuracy)

        print(f"Model Accuracy: {accuracy:.4f}")
        return accuracy


if __name__ == "__main__":
    train_and_evaluate()
