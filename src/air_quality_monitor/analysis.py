from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
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

    def plot_line_chart(self, df: pd.DataFrame, x_axis: str, y_axis: str, title=None) -> plt.Figure:

        if x_axis not in df.columns:
            raise ValueError(f"Invalid column name: {x_axis}")
        elif y_axis not in df.columns:
            raise ValueError(f"Invalid column name: {y_axis}")

        title = f"{y_axis} over time" if title is None else title

        fig, ax = plt.subplots()
        ax.plot(df[x_axis], df[y_axis])

        ax.set(xlabel=x_axis.replace("_", " ").title(), ylabel=y_axis.replace("_", " ").title(), title=title)
        ax.grid()

        return fig


class AirQualityAnalyser(Analyser):
    timestamp_col = "pollutant_timestamp"

    def get_aqi_by_date_range(self, start_date=None, end_date=None) -> pd.DataFrame:
        filtered = self.filter_by_date_range(start_date, end_date)
        return filtered.df[[self.timestamp_col, "aqi"]]


class WeatherAnalyser(Analyser):
    timestamp_col = "dt"

    def get_weather_by_date_range(self, start_date=None, end_date=None) -> pd.DataFrame:
        pass
