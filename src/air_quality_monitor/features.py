import logging

import pandas as pd

from .storage import BaseStorage


class FeatureEngineer:
    def __init__(self, aqi_storage: BaseStorage, weather_storage: BaseStorage):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.aqi_storage = aqi_storage
        self.weather_storage = weather_storage

    def build(self) -> pd.DataFrame:
        self.logger.debug("Executing method")
        aqi_df = self.aqi_storage.read()
        we_df = self.weather_storage.read()

        # Ensure joining timestamps are on the hour
        self.logger.debug("Flooring timestamps to the hour for joining")
        aqi_df["pollutant_timestamp"] = aqi_df["pollutant_timestamp"].dt.floor("h")
        we_df["collected_at"] = we_df["collected_at"].dt.floor("h")
        we_df["forecast_for"] = we_df["forecast_for"].dt.floor("h")

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
        joined_df = self._encode_categoricals(joined_df)

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
                "state_aqi",
                "country_aqi",
                "latitude_aqi",
                "longitude_aqi",
                "timezone_aqi",
                "id_we",
                "forecast_for",
                "weather_main",
                "weather_desc",
                "collected_at_we",
                "state_we",
                "country_we",
                "latitude_we",
                "longitude_we",
                "timezone_we",
            ],
            axis=1,
        )

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

        """
        # Group by city and create lag features
        # aqi_lag_1h is measured AQI one hour ago, etc.
        df["aqi_lag_1h"] = df.groupby("city")["aqi"].shift(1)
        df["aqi_lag_2h"] = df.groupby("city")["aqi"].shift(2)
        df["aqi_lag_4h"] = df.groupby("city")["aqi"].shift(4)
        df["aqi_lag_8h"] = df.groupby("city")["aqi"].shift(8)
        df["aqi_lag_12h"] = df.groupby("city")["aqi"].shift(12)
        df["aqi_lag_24h"] = df.groupby("city")["aqi"].shift(24)
        df["aqi_lag_48h"] = df.groupby("city")["aqi"].shift(48)
        """

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

    def _encode_categoricals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Performs one-hot encoding of categorical variables"""
        self.logger.debug("Executing method")

        df = pd.get_dummies(df, columns=["city", "main_pollutant"])

        return df
