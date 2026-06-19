import os

MODEL_MODE = "ml"
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
MODEL_URI = "models:/qr-safety-model@champion"

TRAIN_FILE_NAME = "train.csv"
TEST_FILE_NAME = "test.csv"
MODEL_NAME = "qr_safety_model.joblib"
ARTIFACT_DIR_NAME = "artifacts"
DATA_DIR_NAME = "data"
