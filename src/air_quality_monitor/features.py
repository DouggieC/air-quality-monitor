"""
Feature engineering for AQI prediction models.

Combines AQI readings with weather forecasts and creates derived features:
- Lag features (AQI at t-1h, t-2h, ..., t-48h)
- Rolling statistics (6h and 24h means/std)
- Temporal features (hour, day_of_week, month)
- Weather trends (temperature/pressure/humidity changes)
- Residual features (30d rolling mean/std by city and horizon, trend)
"""

import logging
from datetime import datetime

import pandas as pd

from .storage import BaseStorage


class FeatureEngineer:
    """Builds feature matrices from AQI, weather, and prediction data.

    Used for both training (full historical data) and prediction
    (recent data filtered by as_of timestamp). Incorporates residual
    feedback from past predictions to help the model learn from its errors.
    """

    def __init__(self, aqi_storage: BaseStorage, weather_storage: BaseStorage, pred_storage: BaseStorage):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.aqi_storage = aqi_storage
        self.weather_storage = weather_storage
        self.pred_storage = pred_storage

    def build(self, as_of: datetime | None = None, include_metadata: bool = False) -> pd.DataFrame:
        """Build feature matrix from AQI, weather, and prediction residual data.

        Args:
            as_of: Reference timestamp for prediction. If None, builds training
                   data from all available history. If set, filters to recent
                   data and creates rows for each prediction horizon.
            include_metadata: If True, retain city/location columns for prediction
                             output. If False, drop them for training.

        Returns:
            DataFrame with features including residual-based features (30d rolling
            mean/std by city and horizon, city trend). Includes 'aqi' column for
            training, excludes it for prediction (as_of is set).
        """
        self.logger.debug("Executing method")

        if as_of is not None:
            as_of = pd.Timestamp(as_of).floor("h")
            filter_aqi = "pollutant_timestamp"
            filter_we = "forecast_for"
            filter_pred = "forecast_for"
            start_aqi = as_of - pd.Timedelta(
                hours=72
            )  # 48 hours required, but leave a margin in case of missing vals
            end_aqi = as_of + pd.Timedelta(hours=1)  # Add an extra hour to allow for flooring
            start_we = as_of - pd.Timedelta(hours=25)  # 24 hours required; allow one for flooring
            end_we = as_of + pd.Timedelta(hours=49)  # Add an extra hour to allow for flooring
            start_pred = as_of - pd.Timedelta(days=30)
            end_pred = as_of + pd.Timedelta(hours=1)  # Add an extra hour to allow for flooring
        else:
            filter_aqi = filter_we = start_aqi = end_aqi = start_we = end_we = start_pred = end_pred = None

        aqi_df = self.aqi_storage.read(time_filter_col=filter_aqi, start=start_aqi, end=end_aqi)
        we_df = self.weather_storage.read(time_filter_col=filter_we, start=start_we, end=end_we)
        pred_df = self.pred_storage.read(time_filter_col=filter_pred, start=start_pred, end=end_pred)

        # Ensure joining timestamps are on the hour
        self.logger.debug("Flooring timestamps to the hour for joining")
        aqi_df["pollutant_timestamp"] = aqi_df["pollutant_timestamp"].dt.floor("h")
        we_df["collected_at"] = we_df["collected_at"].dt.floor("h")
        we_df["forecast_for"] = we_df["forecast_for"].dt.floor("h")
        pred_df["collected_at"] = pred_df["collected_at"].dt.floor("h")
        pred_df["forecast_for"] = pred_df["forecast_for"].dt.floor("h")

        # IQAir doesn't necessarily produce a reading every hour, meaning duplicates on city, pollutant_timestamp, with collected_at an hour apart. Need to deduplicate
        aqi_df = aqi_df.sort_values("collected_at").drop_duplicates(
            subset=["city", "pollutant_timestamp"], keep="last"
        )

        self.logger.debug(
            f"aqi_df pollutant_timestamp range: {aqi_df['pollutant_timestamp'].min()} to {aqi_df['pollutant_timestamp'].max()}"
        )
        self.logger.debug(
            f"we_df forecast_for range: {we_df['forecast_for'].min()} to {we_df['forecast_for'].max()}"
        )
        self.logger.debug(f"as_of: {as_of}")

        # Save full history before filtering
        aqi_full = aqi_df
        we_full = we_df

        # Filter by as_of date if required
        if as_of is not None:
            self.logger.debug(f"Filtering AQI and weather dataframes by as_of={as_of}")
            horizons = [0, 1, 2, 4, 8, 12, 24, 47]  # Can't guarantee availability of forecast @ +48h
            target_times = [as_of + pd.Timedelta(hours=h) for h in horizons]

            aqi_df = aqi_df[
                (aqi_df["pollutant_timestamp"] <= as_of)
                & (aqi_df["pollutant_timestamp"] >= as_of - pd.Timedelta(hours=48))
            ]
            aqi_df = aqi_df.sort_values("pollutant_timestamp").drop_duplicates(subset=["city"], keep="last")

            we_df = we_df[we_df["forecast_for"].isin(target_times)]
            we_df = we_df.sort_values("collected_at").drop_duplicates(
                subset=["city", "forecast_for"], keep="last"
            )

            pred_df = pred_df[
                (pred_df["forecast_for"] <= as_of)
                & (pred_df["forecast_for"] >= as_of - pd.Timedelta(days=30))
            ]

        # Sort the dataframe by city and pollutant_timestamp ready for creating engineered features
        self.logger.debug("Sorting AQI dataframe by city and pollutant_timestamp")
        aqi_df = aqi_df.sort_values(by=["city", "pollutant_timestamp"])

        self.logger.debug("Joining AQI and weather dataframes on city and timestamp")
        left_join_condition = ["city"] if as_of else ["city", "pollutant_timestamp"]
        right_join_condition = ["city"] if as_of else ["city", "forecast_for"]
        joined_df = pd.merge(
            aqi_df,
            we_df,
            left_on=left_join_condition,
            right_on=right_join_condition,
            how="inner",
            suffixes=("_aqi", "_we"),
        )

        joined_df["ref_time"] = as_of if as_of is not None else joined_df["collected_at_we"]

        # Create AQI lag & rolling features
        self.logger.debug("Creating engineered features")
        joined_df = self._create_lag_features(joined_df, aqi_full)
        joined_df = self._create_rolling_features(joined_df, aqi_full)
        joined_df = self._create_temporal_features(joined_df)
        joined_df = self._create_weather_trends(joined_df, we_full)
        joined_df = self._create_residual_features(joined_df, pred_df)
        joined_df = self._encode_categoricals(joined_df, include_metadata)

        # Drop unnecessary columns
        joined_df = joined_df.drop(
            [
                "id_aqi",
                "pollutant_timestamp",
                "temperature_aqi",
                "humidity_aqi",
                "pressure_aqi",
                "heat_index",
                "wind_speed_aqi",
                "wind_direction_aqi",
                "weather_timestamp",
                "collected_at_aqi",
                "id_we",
                "weather_main",
                "weather_desc",
                "state_we",
                "country_we",
                "latitude_we",
                "longitude_we",
                "timezone_we",
                "ref_time",
            ],
            axis=1,
        )

        if not include_metadata:
            # We're training or tuning. Don't need location data or forecast_for
            joined_df = joined_df.drop(
                [
                    "state_aqi",
                    "country_aqi",
                    "latitude_aqi",
                    "longitude_aqi",
                    "timezone_aqi",
                    "forecast_for",
                ],
                axis=1,
            )
        else:
            # We're predicting. Keep location data and forecast_for, but rename
            joined_df = joined_df.rename(
                columns={
                    "state_aqi": "state",
                    "country_aqi": "country",
                    "latitude_aqi": "latitude",
                    "longitude_aqi": "longitude",
                    "timezone_aqi": "timezone",
                }
            )

        # Rename for neatness
        joined_df = joined_df.rename(columns={"collected_at_we": "collected_at"})

        self.logger.info(
            f"Feature engineering complete: {len(joined_df)} rows for {joined_df['city'].nunique()} cities"
        )

        return joined_df

    def _create_lag_features(self, df: pd.DataFrame, aqi_df: pd.DataFrame) -> pd.DataFrame:
        """Add historical AQI values as features (aqi_lag_1h, aqi_lag_2h, etc.)."""
        self.logger.debug("Executing method")

        # Keep only columns needed for lookup
        aqi_lookup = aqi_df[["city", "pollutant_timestamp", "aqi"]].copy()

        lags = [0, 1, 2, 4, 8, 12, 24, 48]
        for lag in lags:
            # Calculate the time we want to look up
            df["_lookup_time"] = df["ref_time"] - pd.Timedelta(hours=lag)

            # Rename AQI column to avoid conflicts
            lookup = aqi_lookup.rename(
                columns={"aqi": f"aqi_lag_{lag}h", "pollutant_timestamp": f"_pt_{lag}"}
            )

            # Merge to get the AQI at that time
            df = df.merge(
                lookup, left_on=["city", "_lookup_time"], right_on=["city", f"_pt_{lag}"], how="left"
            )

            # Drop temp columns
            df = df.drop(columns=["_lookup_time", f"_pt_{lag}"])

        # Rename lag 0 to current for easy reading
        df = df.rename(columns={"aqi_lag_0h": "aqi_current"})

        return df

    def _create_rolling_features(self, df: pd.DataFrame, aqi_df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling statistics (6h/24h mean and std of AQI)."""
        self.logger.debug("Executing method")

        # Sort, group by city and create rolling features
        # aqi_rolling_mean_6h: Mean AQI over the last 6 hours
        # aqi_rolling_std_6h: Std deviation over the last 6 hours
        # aqi_rolling_mean_24h: Mean AQI over the last 24 hours
        aqi_df = aqi_df.sort_values(["city", "pollutant_timestamp"])
        aqi_rolling_mean_6h = (
            aqi_df.groupby("city").rolling("6h", min_periods=3, on="pollutant_timestamp")["aqi"].mean()
        )
        aqi_rolling_std_6h = (
            aqi_df.groupby("city").rolling("6h", min_periods=3, on="pollutant_timestamp")["aqi"].std()
        )
        aqi_rolling_mean_24h = (
            aqi_df.groupby("city").rolling("24h", min_periods=12, on="pollutant_timestamp")["aqi"].mean()
        )

        # Merge into joined df
        aqi_lookup = pd.DataFrame(
            {
                "aqi_rolling_mean_6h": aqi_rolling_mean_6h,
                "aqi_rolling_std_6h": aqi_rolling_std_6h,
                "aqi_rolling_mean_24h": aqi_rolling_mean_24h,
            }
        ).reset_index()

        aqi_lookup = aqi_lookup.rename(columns={"pollutant_timestamp": "_pt_rolling"})

        df = df.merge(
            aqi_lookup,
            left_on=["city", "ref_time"],
            right_on=["city", "_pt_rolling"],
            how="left",
        )

        # Drop temp column
        df = df.drop(columns=["_pt_rolling"])

        return df

    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features: horizon, hour, day_of_week, month."""
        self.logger.debug("Executing method")

        df["horizon"] = (df["forecast_for"] - df["ref_time"]) / pd.Timedelta(hours=1)
        df["hour"] = df["forecast_for"].dt.hour
        df["day_of_week"] = df["forecast_for"].dt.dayofweek
        df["month"] = df["forecast_for"].dt.month

        return df

    def _encode_categoricals(self, df: pd.DataFrame, include_metadata: bool = False) -> pd.DataFrame:
        """One-hot encode city and main_pollutant columns."""
        self.logger.debug("Executing method")

        if include_metadata:
            # We're predicting. Keep city name
            city_col = df["city"].copy()

        # OHE of city & main_pollutant
        df = pd.get_dummies(df, columns=["city", "main_pollutant"])

        if include_metadata:
            # We're predicting. Keep city name
            df["city"] = city_col

        return df

    def _create_weather_trends(self, df: pd.DataFrame, we_df: pd.DataFrame) -> pd.DataFrame:
        """Add weather change features (temp_change_24h, pressure_change_6h, etc.)."""
        self.logger.debug("Executing method")

        current = we_df[we_df["forecast_for"] == we_df["collected_at"]][
            ["city", "collected_at", "temperature", "pressure", "humidity"]
        ].drop_duplicates(subset=["city", "collected_at"])

        trends = [
            # source column, lag hours, new column
            ("temperature", 24, "temp_change_24h"),
            ("pressure", 6, "pressure_change_6h"),
            ("pressure", 24, "pressure_change_24h"),
            ("humidity", 24, "humidity_change_24h"),
        ]

        for source_col, lag, new_col in trends:
            self.logger.debug(f"Processing {source_col}, {lag}, {new_col}")
            # Calculate the time we want to look up
            df["_lookup_time"] = df["ref_time"] - pd.Timedelta(hours=lag)

            # Rename weather feature & timestamp column to avoid conflicts
            lookup = current[["city", "collected_at", source_col]].rename(
                columns={"collected_at": f"_ca_{lag}", source_col: f"_past_{source_col}"}
            )

            df = df.merge(
                lookup, left_on=["city", "_lookup_time"], right_on=["city", f"_ca_{lag}"], how="left"
            )

            df[new_col] = df[f"{source_col}_we"] - df[f"_past_{source_col}"]

            # Drop temp columns
            df = df.drop(columns=["_lookup_time", f"_ca_{lag}", f"_past_{source_col}"])

        return df

    def _create_residual_features(self, df: pd.DataFrame, pred_df: pd.DataFrame) -> pd.DataFrame:
        """Add residual-based features from historical prediction accuracy.

        Creates rolling 30-day statistics from past prediction residuals:
        - residual_rolling_mean_by_city_30d: Average prediction error per city
        - residual_rolling_std_by_city_30d: Error volatility per city
        - residual_trend_by_city: Change in error (7d mean - 30d mean)
        - residual_rolling_mean_by_horizon_30d: Average error per forecast horizon
        - residual_rolling_std_by_horizon_30d: Error volatility per horizon
        """
        self.logger.debug("Executing method")

        pred_filtered = pred_df[pred_df["residual"].notna()]
        self.logger.info(f"Found {len(pred_filtered)} predictions with residuals")
        pred_filtered = pred_filtered.sort_values(["city", "forecast_for"])

        # Aggregate by city+forecast_for before rolling to avoid merge explosion
        pred_city = pred_filtered.groupby(["city", "forecast_for"])["residual"].mean().reset_index()

        city_mean = (
            pred_city.groupby("city").rolling("30d", min_periods=10, on="forecast_for")["residual"].mean()
        ).reset_index()
        city_mean = city_mean.rename(columns={"residual": "residual_rolling_mean_by_city_30d"})

        city_mean_7d = (
            pred_city.groupby("city").rolling("7d", min_periods=3, on="forecast_for")["residual"].mean()
        ).reset_index()
        city_mean_7d = city_mean_7d.rename(
            columns={"residual": "residual_rolling_mean_by_city_7d", "forecast_for": "_ff_m7d"}
        )

        city_std = (
            pred_city.groupby("city").rolling("30d", min_periods=10, on="forecast_for")["residual"].std()
        ).reset_index()
        city_std = city_std.rename(
            columns={"residual": "residual_rolling_std_by_city_30d", "forecast_for": "_ff_std"}
        )

        city_lookup = city_mean.merge(
            city_mean_7d, left_on=["city", "forecast_for"], right_on=["city", "_ff_m7d"]
        ).merge(city_std, left_on=["city", "forecast_for"], right_on=["city", "_ff_std"])

        # Calculate trend
        city_lookup["residual_trend_by_city"] = (
            city_lookup["residual_rolling_mean_by_city_7d"] - city_lookup["residual_rolling_mean_by_city_30d"]
        )
        city_lookup = city_lookup.drop(columns=["residual_rolling_mean_by_city_7d", "_ff_m7d", "_ff_std"])
        self.logger.debug(f"Built city residual lookup with {len(city_lookup)} rows")

        city_lookup = city_lookup.rename(columns={"forecast_for": "_ff_lookup"})
        df = df.merge(
            city_lookup,
            left_on=["city", "ref_time"],
            right_on=["city", "_ff_lookup"],
            how="left",
        )
        df = df.drop(columns=["_ff_lookup"])

        pred_filtered = pred_filtered.sort_values(["horizon", "forecast_for"])
        # Aggregate by horizon+forecast_for before rolling
        pred_horizon = pred_filtered.groupby(["horizon", "forecast_for"])["residual"].mean().reset_index()

        horizon_mean = (
            pred_horizon.groupby("horizon")
            .rolling("30d", min_periods=10, on="forecast_for")["residual"]
            .mean()
        ).reset_index()
        horizon_mean = horizon_mean.rename(columns={"residual": "residual_rolling_mean_by_horizon_30d"})

        horizon_std = (
            pred_horizon.groupby("horizon")
            .rolling("30d", min_periods=10, on="forecast_for")["residual"]
            .std()
        ).reset_index()
        horizon_std = horizon_std.rename(
            columns={"residual": "residual_rolling_std_by_horizon_30d", "forecast_for": "_ff_std"}
        )

        horizon_lookup = horizon_mean.merge(
            horizon_std, left_on=["horizon", "forecast_for"], right_on=["horizon", "_ff_std"]
        )
        horizon_lookup = horizon_lookup.drop(columns=["_ff_std"])
        self.logger.debug(f"Built horizon residual lookup with {len(horizon_lookup)} rows")

        horizon_lookup = horizon_lookup.rename(columns={"forecast_for": "_ff_lookup"})
        df = df.merge(
            horizon_lookup,
            left_on=["horizon", "ref_time"],
            right_on=["horizon", "_ff_lookup"],
            how="left",
        )
        df = df.drop(columns=["_ff_lookup"])

        return df
