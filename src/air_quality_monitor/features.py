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

        # Drop unnecessary columns (only need location data once)
        aqi_df = aqi_df.drop(["id"], axis=1)
        we_df = we_df.drop(["id", "state", "country", "latitude", "longitude", "timezone"], axis=1)

        # Ensure joining timestamps are on the hour
        self.logger.debug("Flooring timestamps to the hour for joining")
        aqi_df["pollutant_timestamp"] = aqi_df["pollutant_timestamp"].dt.floor("h")
        we_df["collected_at"] = we_df["collected_at"].dt.floor("h")
        we_df["forecast_for"] = we_df["forecast_for"].dt.floor("h")

        # Sort the dataframeby city and pollutant_timestamp ready for creating engineered features
        self.logger.debug("Sorting AQI dataframe by city and pollutant_timestamp")
        aqi_df = aqi_df.sort_values(by=["city", "pollutant_timestamp"])

        # Create AQI lag & rolling features
        self.logger.debug("Creating AQI lag and rolling features")
        aqi_df = self._create_lag_features(aqi_df)
        aqi_df = self._create_rolling_features(aqi_df)

        self.logger.debug("Joining AQI and weather dataframes on city and timestamp")
        joined_df = pd.merge(
            aqi_df,
            we_df,
            left_on=["city", "pollutant_timestamp"],
            right_on=["city", "collected_at"],
            how="inner",
            suffixes=("_aqi", "_we"),
        )

        # Work out the horizon for each row
        joined_df["horizon"] = (joined_df["forecast_for"] - joined_df["collected_at_we"]) / pd.Timedelta(
            hours=1
        )

        return joined_df

    def _create_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assumes df is sorted by city and pollutant_timestamp"""
        self.logger.debug("Executing method")

        # Group by city and create lag features
        # aqi_lag_1h is measured AQI one hour ago, etc.
        df["aqi_lag_1h"] = df.groupby("city")["aqi"].shift(1)
        df["aqi_lag_2h"] = df.groupby("city")["aqi"].shift(2)
        df["aqi_lag_4h"] = df.groupby("city")["aqi"].shift(4)
        df["aqi_lag_8h"] = df.groupby("city")["aqi"].shift(8)
        df["aqi_lag_12h"] = df.groupby("city")["aqi"].shift(12)
        df["aqi_lag_24h"] = df.groupby("city")["aqi"].shift(24)
        df["aqi_lag_48h"] = df.groupby("city")["aqi"].shift(48)

        return df

    def _create_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assumes df is sorted by city and pollutant_timestamp"""
        self.logger.debug("Executing method")

        # Group by city and create rolling features
        # aqi_rolling_mean_6h: Mean AQI over the last 6 hours
        # aqi_rolling_std_6h: Std deviation over the last 6 hours
        # aqi_rolling_mean_24h: Mean AQI over the last 24 hours
        df["aqi_rolling_mean_6h"] = df.groupby("city")["aqi"].rolling(6).mean().reset_index(0, drop=True)
        df["aqi_rolling_std_6h"] = df.groupby("city")["aqi"].rolling(6).std().reset_index(0, drop=True)
        df["aqi_rolling_mean_24h"] = df.groupby("city")["aqi"].rolling(24).mean().reset_index(0, drop=True)

        return df
