from __future__ import annotations

from typing import TypedDict

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from app.config import MLFLOW_TRACKING_URI, MODEL_URI

_model = None


class ModelInfo(TypedDict):
    run_id: str
    model_type: str
    test_accuracy: float


def load_model():
    global _model
    if _model is None:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        _model = mlflow.sklearn.load_model(MODEL_URI)
    return _model


def get_model_info() -> ModelInfo:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    model_version = client.get_model_version_by_alias("qr-safety-model", "champion")
    run = client.get_run(model_version.run_id)
    return {
        "run_id": model_version.run_id,
        "model_type": run.data.params.get("model_type", ""),
        "test_accuracy": float(run.data.metrics.get("test_accuracy", 0.0)),
    }
