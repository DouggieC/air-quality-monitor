import logging
from datetime import datetime

import mlflow

from .features import FeatureEngineer
from .models import Prediction


class Predictor:
    def __init__(self, feature_engineer: FeatureEngineer):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.feature_engineer = feature_engineer
        self.models = {
            "short": mlflow.pyfunc.load_model("models:/lightgbm_short/Production"),
            "medium": mlflow.pyfunc.load_model("models:/lightgbm_medium/Production"),
            "long": mlflow.pyfunc.load_model("models:/lightgbm_long/Production"),
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
        features_df = self.feature_engineer.build(as_of=datetime.now(), include_metadata=True)  # noqa: DTZ005
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
                axis=1,
            )
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
