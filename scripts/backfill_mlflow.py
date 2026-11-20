import joblib
import mlflow
from mlflow.tracking import MlflowClient

from air_quality_monitor.config import Config

models_to_backfill = [
    ("lightgbm_short", "lightgbm_short_latest.joblib"),
    ("lightgbm_medium", "lightgbm_medium_latest.joblib"),
    ("lightgbm_long", "lightgbm_long_latest.joblib"),
    ("xgboost_short", "xgboost_short_latest.joblib"),
    ("xgboost_medium", "xgboost_medium_latest.joblib"),
    ("xgboost_long", "xgboost_long_latest.joblib"),
]

mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
client = MlflowClient()

for model, filename in models_to_backfill:
    print(f"Processing model {model}, filename {filename}")
    loaded_model = joblib.load(f"models/{filename}")

    # Get the model type from the name prefix
    model_type = model.split("_", 1)[0]

    # Register the model with MLflow
    with mlflow.start_run(run_name=f"backfill_{model}"):
        getattr(mlflow, model_type).log_model(loaded_model, "model", registered_model_name=model)

        client.set_registered_model_alias(model, "v2026_11", version=1)
        client.set_registered_model_alias(model, "production", version=1)
