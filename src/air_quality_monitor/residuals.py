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
        merged_df = pd.merge(
            obs_df, pred_df, left_on=["city", "pollutant_timestamp"], right_on=["city", "forecast_for"]
        )
        self.logger.info(f"Matched {len(merged_df)} predictions to observations")

        # Compute residuals: actual - predicted
        merged_df["actual_aqi"] = merged_df["aqi"]
        merged_df["residual"] = merged_df["actual_aqi"] - merged_df["predicted_aqi"]

        # Update each matched prediction
        update_count = 0
        for _, row in merged_df.iterrows():
            # Build filter to identify the row - differs by storage type
            if isinstance(self.pred_storage, DBStorage):
                filters = {"id": row["id"]}
            elif isinstance(self.pred_storage, CSVStorage):
                filters = {
                    "city": row["city"],
                    "forecast_for": row["forecast_for"],
                    "model_name": row["model_name"],
                    "horizon": row["horizon"],
                }
            else:
                raise TypeError(f"Unsupported storage type: {type(self.pred_storage)}")

            updates = {"actual_aqi": row["actual_aqi"], "residual": row["residual"]}
            self.pred_storage.update(filters, updates)
            update_count += 1

        self.logger.info(f"Updated {update_count} predictions with residuals")
        return update_count
