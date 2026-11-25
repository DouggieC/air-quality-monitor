"""
Residual calculation and backfilling for AQI predictions.

Computes prediction residuals (actual - predicted) by matching predictions
to observations once actuals become available.
"""

import logging
from datetime import UTC, datetime

import pandas as pd

from .storage import BaseStorage, CSVStorage, DBStorage


class ResidualHandler:
    """Handles residual computation and backfilling for predictions.

    Matches predictions to actual observations and computes residuals
    to enable prediction accuracy tracking and feedback features.
    """

    def __init__(self, obs_storage: BaseStorage, pred_storage: BaseStorage):
        """Initialise with storage backends for observations and predictions.

        Args:
            obs_storage: Storage backend for AQI observations (actuals).
            pred_storage: Storage backend for predictions (to read and update).
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.pred_storage = pred_storage
        self.obs_storage = obs_storage

    def backfill(self, as_of: datetime | None = None) -> int:
        """Backfill residuals for predictions whose actuals are now available.

        Finds predictions where forecast_for < as_of and residual is NULL,
        matches them to observations, computes residuals, and updates storage.

        Args:
            as_of: Cutoff time for backfilling. Predictions with forecast_for
                   before this time are eligible. Defaults to now.

        Returns:
            Number of predictions updated.

        Raises:
            TypeError: If observation and prediction storage types don't match.
        """
        self.logger.debug("Executing method")
        as_of = datetime.now(UTC) if as_of is None else as_of

        if type(self.pred_storage) is not type(self.obs_storage):
            raise TypeError(f"{self.pred_storage} and {self.obs_storage} must be of the same type")

        obs_df = self.obs_storage.read()
        pred_df = self.pred_storage.read()
        self.logger.info(f"Read {len(obs_df)} observations and {len(pred_df)} predictions")

        # Filter to predictions needing backfill: no residual yet and target time has passed
        pred_df = pred_df[(pred_df["residual"].isna()) & (pred_df["forecast_for"] < as_of)]
        self.logger.info(f"Found {len(pred_df)} predictions needing backfill")

        if pred_df.empty:
            self.logger.info("No predictions to backfill")
            return 0

        # Match predictions to observations on city and timestamp
        obs_df = obs_df.drop(columns=["id"], errors="ignore")  # Only exists in DB; ignore if CSV
        obs_df = obs_df.sort_values("collected_at").drop_duplicates(
            subset=["city", "pollutant_timestamp"], keep="last"
        )
        merged_df = pd.merge(
            obs_df, pred_df, left_on=["city", "pollutant_timestamp"], right_on=["city", "forecast_for"]
        )
        self.logger.info(f"Matched {len(merged_df)} predictions to observations")

        # Compute residuals: actual - predicted
        merged_df["actual_aqi"] = merged_df["aqi"]
        merged_df["residual"] = merged_df["actual_aqi"] - merged_df["predicted_aqi"]

        # Update all matched predictions
        if isinstance(self.pred_storage, DBStorage):
            # Build list of dicts with id & update values
            updates = merged_df[["id", "actual_aqi", "residual"]].to_dict("records")
            self.pred_storage.bulk_update(updates)
        elif isinstance(self.pred_storage, CSVStorage):
            # Build DF with key columns & update columns
            key_columns = ["city", "forecast_for", "model_name", "horizon"]
            updates_df = merged_df[key_columns + ["actual_aqi", "residual"]]
            self.pred_storage.bulk_update(updates_df, key_columns)
        else:
            raise TypeError(f"Unsupported storage type: {type(self.pred_storage)}")

        update_count = len(merged_df)

        self.logger.info(f"Updated {update_count} predictions with residuals")
        return update_count
