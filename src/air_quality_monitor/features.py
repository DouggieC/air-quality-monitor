import logging
from datetime import datetime

import pandas as pd

from .storage import BaseStorage


class FeatureEngineer:
    def __init__(self, aqi_storage: BaseStorage, weather_storage: BaseStorage):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.aqi_storage = aqi_storage
        self.weather_storage = weather_storage

    def build(self, as_of: datetime | None = None, include_metadata: bool = False) -> pd.DataFrame:
        self.logger.debug("Executing method")
        aqi_df = self.aqi_storage.read()
        we_df = self.weather_storage.read()

        # Ensure joining timestamps are on the hour
        self.logger.debug("Flooring timestamps to the hour for joining")
        aqi_df["pollutant_timestamp"] = aqi_df["pollutant_timestamp"].dt.floor("h")
        we_df["collected_at"] = we_df["collected_at"].dt.floor("h")
        we_df["forecast_for"] = we_df["forecast_for"].dt.floor("h")

        # Filter by as_of date if required
        if as_of is not None:
            self.logger.debug(f"Filtering AQI and weather dataframes by as_of={as_of}")
            aqi_df = aqi_df[
                (aqi_df["pollutant_timestamp"] <= as_of)
                & (aqi_df["pollutant_timestamp"] >= as_of - pd.Timedelta(hours=48))
            ]
            we_df = we_df[
                (we_df["forecast_for"] >= as_of) & (we_df["forecast_for"] <= as_of + pd.Timedelta(hours=48))
            ]

        # Sort the dataframeby city and pollutant_timestamp ready for creating engineered features
        self.logger.debug("Sorting AQI dataframe by city and pollutant_timestamp")
        aqi_df = aqi_df.sort_values(by=["city", "pollutant_timestamp"])

        self.logger.debug("Joining AQI and weather dataframes on city and timestamp")
        joined_df = pd.merge(
            aqi_df,
            we_df,
            left_on=["city", "pollutant_timestamp"],
            right_on=["city", "forecast_for"],
            how="inner",
            suffixes=("_aqi", "_we"),
        )

        # Create AQI lag & rolling features
        self.logger.debug("Creating engineered features")
        joined_df = self._create_lag_features(joined_df, aqi_df)
        joined_df = self._create_rolling_features(joined_df, aqi_df)
        joined_df = self._create_temporal_features(joined_df)
        joined_df = self._create_weather_trends(joined_df)
        joined_df = self._encode_categoricals(joined_df, include_metadata)

        # Drop unnecessary columns
        joined_df = joined_df.drop(
            [
                "id_aqi",
                "pollutant_timestamp",
                "temperature_aqi",
                "humidity_aqi",
                "pressure_aqi",
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
        return joined_df

    def _create_lag_features(self, df: pd.DataFrame, aqi_df: pd.DataFrame) -> pd.DataFrame:
        """Assumes df is sorted by city and pollutant_timestamp"""
        self.logger.debug("Executing method")

        # Keep only columns needed for lookup
        aqi_lookup = aqi_df[["city", "pollutant_timestamp", "aqi"]].copy()

        lags = [0, 1, 2, 4, 8, 12, 24, 48]
        for lag in lags:
            # Calculate the time we want to look up
            df["_lookup_time"] = df["collected_at_we"] - pd.Timedelta(hours=lag)

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
        self.logger.debug("Executing method")

        # Sort, group by city and create rolling features
        # aqi_rolling_mean_6h: Mean AQI over the last 6 hours
        # aqi_rolling_std_6h: Std deviation over the last 6 hours
        # aqi_rolling_mean_24h: Mean AQI over the last 24 hours
        aqi_df = aqi_df.sort_values(["city", "pollutant_timestamp"])
        aqi_df["aqi_rolling_mean_6h"] = (
            aqi_df.groupby("city")["aqi"].rolling(6).mean().reset_index(0, drop=True)
        )
        aqi_df["aqi_rolling_std_6h"] = (
            aqi_df.groupby("city")["aqi"].rolling(6).std().reset_index(0, drop=True)
        )
        aqi_df["aqi_rolling_mean_24h"] = (
            aqi_df.groupby("city")["aqi"].rolling(24).mean().reset_index(0, drop=True)
        )

        # Merge into joined df
        aqi_lookup = aqi_df[
            [
                "city",
                "pollutant_timestamp",
                "aqi_rolling_mean_6h",
                "aqi_rolling_std_6h",
                "aqi_rolling_mean_24h",
            ]
        ]

        aqi_lookup = aqi_lookup.rename(columns={"pollutant_timestamp": "_pt_rolling"})

        df = df.merge(
            aqi_lookup,
            left_on=["city", "collected_at_we"],
            right_on=["city", "_pt_rolling"],
            how="left",
        )

        # Drop temp column
        df = df.drop(columns=["_pt_rolling"])

        return df

    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assumes df is sorted by city"""
        self.logger.debug("Executing method")

        df["horizon"] = (df["forecast_for"] - df["collected_at_we"]) / pd.Timedelta(hours=1)
        df["hour"] = df["forecast_for"].dt.hour
        df["day_of_week"] = df["forecast_for"].dt.dayofweek
        df["month"] = df["forecast_for"].dt.month

        return df

    def _encode_categoricals(self, df: pd.DataFrame, include_metadata: bool = False) -> pd.DataFrame:
        """Performs one-hot encoding of categorical variables"""
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

    def _create_weather_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.debug("Executing method")

        current = df[df["horizon"] == 0][
            ["city", "collected_at_we", "temperature_we", "pressure_we", "humidity_we"]
        ].drop_duplicates(subset=["city", "collected_at_we"])

        trends = [
            # source column, lag hours, new column
            ("temperature_we", 24, "temp_change_24h"),
            ("pressure_we", 6, "pressure_change_6h"),
            ("pressure_we", 24, "pressure_change_24h"),
            ("humidity_we", 24, "humidity_change_24h"),
        ]

        for source_col, lag, new_col in trends:
            self.logger.debug(f"Processing {source_col}, {lag}, {new_col}")
            # Calculate the time we want to look up
            df["_lookup_time"] = df["collected_at_we"] - pd.Timedelta(hours=lag)

            # Rename weather feature & timestamp column to avoid conflicts
            lookup = current[["city", "collected_at_we", source_col]].rename(
                columns={"collected_at_we": f"_ca_{lag}", source_col: f"_past_{source_col}"}
            )

            df = df.merge(
                lookup, left_on=["city", "_lookup_time"], right_on=["city", f"_ca_{lag}"], how="left"
            )

            df[new_col] = df[source_col] - df[f"_past_{source_col}"]

            # Drop temp columns
            df = df.drop(columns=["_lookup_time", f"_ca_{lag}", f"_past_{source_col}"])

        return df
