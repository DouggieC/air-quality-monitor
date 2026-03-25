from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import pandas as pd


class Analyser(ABC):
    """
    Dataframes could be AQI data:
        "city","state","country","latitude","longitude",
        "aqi","main_pollutant","pollutant_timestamp",
        "temperature","humidity","pressure","wind_speed",
        "wind_direction","heat_index","weather_timestamp","collected_at"

    Or OWM data:
        "city","state","country","latitude","longitude",
        "dt","sunrise","sunset","temperature","feels_like",
        "pressure","humidity","dew_point","uvi","clouds",
        "visibility","wind_speed","wind_direction","wind_gust",
        "rain","snow","weather_main","weather_desc","collected_at"
    """

    def __init__(self, df: pd.DataFrame):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")

        self.df = df

    @property
    @abstractmethod
    def timestamp_col(self):
        pass

    def filter_by_city(self, city) -> Analyser:
        self.logger.debug("Executing method")
        # TODO: What constitutes a 'city'? Just a name? Or a City object?
        # Assume it's a name for now, and exists in the dataset
        df_filtered = self.df[self.df["city"] == city]

        return self.__class__(df_filtered)

    def filter_by_date_range(self, start_date=None, end_date=None) -> Analyser:
        self.logger.debug("Executing method")

        start_date = self.df[self.timestamp_col].min if start_date is None else start_date
        end_date = self.df[self.timestamp_col].max if end_date is None else end_date

        df_filtered = self.df[
            (self.df[self.timestamp_col] >= start_date) & (self.df[self.timestamp_col] <= end_date)
        ]

        return self.__class__(df_filtered)


class AirQualityAnalyser(Analyser):
    timestamp_col = "pollutant_timestamp"


class WeatherAnalyser(Analyser):
    timestamp_col = "dt"
