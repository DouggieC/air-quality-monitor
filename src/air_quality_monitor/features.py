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

        # print(aqi_df.info())
        # print(we_df.info())

        # Ensure joining timestamps are on the hour
        self.logger.debug("Flooring timestamps to the hour for joining")
        aqi_df["pollutant_timestamp"] = aqi_df["pollutant_timestamp"].dt.floor("h")
        we_df["collected_at"] = we_df["collected_at"].dt.floor("h")

        # Create AQI lag features
        aqi_df = self._create_lag_features(aqi_df)

        # print(f"aqi_df['pollutant_timestamp']: {aqi_df['pollutant_timestamp'].head()}")
        # print(f"we_df['collected_at']: {we_df['collected_at'].head()}")

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

        # print(f"Joined dataframe shape: {joined_df.shape}")
        # print(f"Joined dataframe columns: {joined_df.columns.tolist()}")
        # print(f"Joined dataframe head: {joined_df.head()}")

        return joined_df

    def _create_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Sort the dataframeby city and pollutant_timestamp
        df = df.sort_values(by=["city", "pollutant_timestamp"])

        # Group by city and create lag features
        df["aqi_lag_1h"] = df.groupby("city")["aqi"].shift(1)
        df["aqi_lag_2h"] = df.groupby("city")["aqi"].shift(2)
        df["aqi_lag_4h"] = df.groupby("city")["aqi"].shift(4)
        df["aqi_lag_8h"] = df.groupby("city")["aqi"].shift(8)
        df["aqi_lag_12h"] = df.groupby("city")["aqi"].shift(12)
        df["aqi_lag_24h"] = df.groupby("city")["aqi"].shift(24)
        df["aqi_lag_48h"] = df.groupby("city")["aqi"].shift(48)

        return df

    def _create_rolling_features(self):
        pass
