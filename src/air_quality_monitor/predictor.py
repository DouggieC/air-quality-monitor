import json
import logging
from datetime import datetime, timezone

import mlflow

from .config import Config
from .features import FeatureEngineer
from .models import Prediction


class Predictor:
    def __init__(self, feature_engineer: FeatureEngineer):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.feature_engineer = feature_engineer
        self.models = {
            "short": mlflow.pyfunc.load_model("models:/lightgbm_short/latest"),
            "medium": mlflow.pyfunc.load_model("models:/lightgbm_medium/latest"),
            "long": mlflow.pyfunc.load_model("models:/lightgbm_long/latest"),
        }

        self.horizon_to_range = {
            0: "short",
            1: "short",
            2: "short",
            4: "medium",
            8: "medium",
            12: "medium",
            24: "long",
            48: "long",
        }

    def predict(self) -> list[Prediction]:
        self.logger.debug("Executing method")
        # Tempfix: No access to up-to-date data
        as_of = datetime(2026, 10, 5, 10, 0, 0, tzinfo=timezone.utc)
        features_df = self.feature_engineer.build(as_of=as_of, include_metadata=True)  # noqa: DTZ005
        # features_df = self.feature_engineer.build(as_of=datetime.now(timezone.utc), include_metadata=True)
        predictions = []

        for range_name, model in self.models.items():
            self.logger.debug(f"Predicting for range: {range_name}")
            # Get horizons for this range
            horizons = [h for h, r in self.horizon_to_range.items() if r == range_name]

            # Filter rows for this range
            mask = features_df["horizon"].isin(horizons)
            batch = features_df[mask]

            # Batch predict
            model_input = batch.drop(
                columns=[
                    "city",
                    "state",
                    "country",
                    "timezone",
                    "latitude",
                    "longitude",
                    "collected_at",
                    "forecast_for",
                ],
            )
            # print(model_input.dtypes[model_input.dtypes == 'object'])
            model_input["heat_index"] = model_input["heat_index"].fillna(0).astype(float)
            # print(f"model_input columns ({len(model_input.columns)}): {sorted(model_input.columns.tolist())}")
            # Load the columns list used for training
            with open(Config.CONFIG_DIR / "training_columns.json", "r") as f:
                training_columns = json.load(f)
            model_input = model_input.reindex(columns=training_columns, fill_value=0)
            print(f"model_input shape: {model_input.shape}")
            print(f"batch shape: {batch.shape}")
            preds = model.predict(model_input)

            for (_, row), pred in zip(batch.iterrows(), preds):
                prediction = Prediction(
                    city=row["city"],
                    state=row["state"],
                    country=row["country"],
                    timezone=row["timezone"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    collected_at=row["collected_at"],
                    forecast_for=row["forecast_for"],
                    predicted_aqi=int(pred),
                    model_name=f"lightgbm_{range_name}",
                    horizon=int(row["horizon"]),
                )
                predictions.append(prediction)

        return predictions
