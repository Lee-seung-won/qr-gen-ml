from __future__ import annotations

from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from app.config import (
    ARTIFACT_DIR_NAME,
    DATA_DIR_NAME,
    MLFLOW_TRACKING_URI,
    MODEL_NAME,
    TEST_FILE_NAME,
    TRAIN_FILE_NAME,
)

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / DATA_DIR_NAME
ARTIFACT_DIR = ML_DIR / ARTIFACT_DIR_NAME

MODELS: dict[str, Pipeline] = {
    "LR": Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    ),
    "NB": Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", MultinomialNB()),
        ]
    ),
    "DT": Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", DecisionTreeClassifier(random_state=42)),
        ]
    ),
}


def load_datasets() -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    train_df = pd.read_csv(DATA_DIR / TRAIN_FILE_NAME)
    test_df = pd.read_csv(DATA_DIR / TEST_FILE_NAME)
    x_train = train_df["text"]
    y_train = train_df["label"]
    x_test = test_df["text"]
    y_test = test_df["label"]
    return x_train, y_train, x_test, y_test


def train_and_log_models(
    x_train: pd.Series,
    y_train: pd.Series,
    x_test: pd.Series,
    y_test: pd.Series,
) -> tuple[str, Pipeline, float]:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("qr-safety")

    best_name = ""
    best_model: Pipeline | None = None
    best_test_accuracy = -1.0

    for name, pipeline in MODELS.items():
        with mlflow.start_run(run_name=name):
            pipeline.fit(x_train, y_train)

            train_pred = pipeline.predict(x_train)
            test_pred = pipeline.predict(x_test)
            train_accuracy = accuracy_score(y_train, train_pred)
            test_accuracy = accuracy_score(y_test, test_pred)

            mlflow.log_param("model_type", name)
            mlflow.log_metric("train_accuracy", train_accuracy)
            mlflow.log_metric("test_accuracy", test_accuracy)
            mlflow.sklearn.log_model(
                pipeline,
                artifact_path="model",
                registered_model_name="qr-safety-model",
            )

            print(
                f"[{name}] train_accuracy={train_accuracy:.4f} "
                f"test_accuracy={test_accuracy:.4f}"
            )

            if test_accuracy > best_test_accuracy:
                best_test_accuracy = test_accuracy
                best_name = name
                best_model = pipeline

    if best_model is None:
        raise RuntimeError("No model was trained.")

    return best_name, best_model, best_test_accuracy


def save_best_model(model: Pipeline) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / MODEL_NAME
    joblib.dump(model, model_path)
    return model_path


def main() -> None:
    x_train, y_train, x_test, y_test = load_datasets()
    best_name, best_model, best_test_accuracy = train_and_log_models(
        x_train, y_train, x_test, y_test
    )
    model_path = save_best_model(best_model)
    print(f"Best model: {best_name} (test_accuracy={best_test_accuracy:.4f})")
    print(f"Saved artifact: {model_path}")


if __name__ == "__main__":
    main()
