import json
import logging
from datetime import UTC, datetime

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

    def predict(self, as_of: datetime | None = None) -> list[Prediction]:
        self.logger.debug("Executing method")
        as_of = datetime.now(UTC) if as_of is None else as_of
        features_df = self.feature_engineer.build(as_of=as_of, include_metadata=True)
        self.logger.debug(f"Total feature rows: {len(features_df)}")
        self.logger.debug(f"Rows per city:\n{features_df['city'].value_counts()}")
        self.logger.debug(f"Unique city/horizon combos: {len(features_df.groupby(['city', 'horizon']))}")
        self.logger.debug(f"Missing values in AQI features: {features_df.filter(like="aqi_").isna().sum()}")

        predictions = []

        for range_name, model in self.models.items():
            self.logger.debug(f"Predicting for range: {range_name}")
            # Get horizons for this range
            horizons = [h for h, r in self.horizon_to_range.items() if r == range_name]

            # Filter rows for this range
            mask = features_df["horizon"].isin(horizons)
            batch = features_df[mask]

            # Don't fail if we have missing data, just log it and move on to the next batch
            if batch.empty:
                self.logger.warning(f"No features rows for {range_name} range (horizons: {horizons}); skipping")
                continue

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
            model_input["heat_index"] = model_input["heat_index"].fillna(0).astype(float)
            
            # Load the columns list used for training
            with open(Config.CONFIG_DIR / "training_columns.json", "r") as f:
                training_columns = json.load(f)
            model_input = model_input.reindex(columns=training_columns, fill_value=0)
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
