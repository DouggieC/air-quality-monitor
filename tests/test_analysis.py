from datetime import datetime, timezone

import pandas as pd
import pytest
from matplotlib.pylab import Figure

from air_quality_monitor.analysis import AirQualityAnalyser


@pytest.fixture
def sample_aqr_df():
    return pd.DataFrame(
        [
            {
                "city": "Sarajevo",
                "state": "Federation of B&H",
                "country": "Bosnia Herzegovina",
                "timezone": "Europe/Sarajevo",
                "latitude": None,
                "longitude": None,
                "aqi": 68,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 9, 0, tzinfo=timezone.utc),  # 2026-03-27 10:00
                "temperature": 2,
                "humidity": 92,
                "pressure": 1002,
                "wind_speed": 1.67,
                "wind_direction": 273,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 9, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 9, 10, 23, 197146, tzinfo=timezone.utc),
            },
            {
                "city": "London",
                "state": "England",
                "country": "United Kingdom",
                "timezone": "Europe/London",
                "latitude": None,
                "longitude": None,
                "aqi": 31,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 9, 0, tzinfo=timezone.utc),  # 2026-03-27 9:00
                "temperature": 9,
                "humidity": 78,
                "pressure": 1021,
                "wind_speed": 3.06,
                "wind_direction": 217,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 9, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 9, 10, 25, 825070, tzinfo=timezone.utc),
            },
            {
                "city": "Sarajevo",
                "state": "Federation of B&H",
                "country": "Bosnia Herzegovina",
                "timezone": "Europe/Sarajevo",
                "latitude": None,
                "longitude": None,
                "aqi": 66,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 10, 0, tzinfo=timezone.utc),  # 2026-03-27 11:00
                "temperature": 2,
                "humidity": 97,
                "pressure": 1003,
                "wind_speed": 1.67,
                "wind_direction": 260,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 10, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 10, 10, 23, 540432, tzinfo=timezone.utc),
            },
            {
                "city": "London",
                "state": "England",
                "country": "United Kingdom",
                "timezone": "Europe/London",
                "latitude": None,
                "longitude": None,
                "aqi": 33,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 10, 0, tzinfo=timezone.utc),  # 2026-03-27 10:00
                "temperature": 10,
                "humidity": 78,
                "pressure": 1021,
                "wind_speed": 3.33,
                "wind_direction": 212,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 10, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 10, 10, 26, 135386, tzinfo=timezone.utc),
            },
            {
                "city": "Sarajevo",
                "state": "Federation of B&H",
                "country": "Bosnia Herzegovina",
                "timezone": "Europe/Sarajevo",
                "latitude": None,
                "longitude": None,
                "aqi": 61,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 11, 0, tzinfo=timezone.utc),  # 2026-03-27 12:00
                "temperature": 2,
                "humidity": 97,
                "pressure": 1003,
                "wind_speed": 1.39,
                "wind_direction": 258,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 11, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 11, 10, 23, 999507, tzinfo=timezone.utc),
            },
            {
                "city": "London",
                "state": "England",
                "country": "United Kingdom",
                "timezone": "Europe/London",
                "latitude": None,
                "longitude": None,
                "aqi": 31,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 11, 0, tzinfo=timezone.utc),  # 2026-03-27 11:00
                "temperature": 12,
                "humidity": 77,
                "pressure": 1020,
                "wind_speed": 3.89,
                "wind_direction": 215,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 11, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 11, 10, 26, 648601, tzinfo=timezone.utc),
            },
            {
                "city": "Sarajevo",
                "state": "Federation of B&H",
                "country": "Bosnia Herzegovina",
                "timezone": "Europe/Sarajevo",
                "latitude": None,
                "longitude": None,
                "aqi": 60,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),  # 2026-03-27 13:00
                "temperature": 5,
                "humidity": 95,
                "pressure": 1003,
                "wind_speed": 1.67,
                "wind_direction": 261,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 12, 10, 24, 514800, tzinfo=timezone.utc),
            },
            {
                "city": "London",
                "state": "England",
                "timezone": "Europe/London",
                "country": "United Kingdom",
                "latitude": None,
                "longitude": None,
                "aqi": 28,
                "main_pollutant": "p2",
                "pollutant_timestamp": datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),  # 2026-03-27 12:00
                "temperature": 11,
                "humidity": 77,
                "pressure": 1020,
                "wind_speed": 4.17,
                "wind_direction": 221,
                "heat_index": None,
                "weather_timestamp": datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
                "collected_at": datetime(2026, 3, 27, 12, 10, 27, 127305, tzinfo=timezone.utc),
            },
        ]
    )


@pytest.fixture
def sample_aqr_df_sj(sample_aqr_df: pd.DataFrame):
    return sample_aqr_df[sample_aqr_df["city"] == "Sarajevo"].reset_index(drop=True)


class TestAirQualityAnalyser:
    @pytest.fixture
    def aqi_analyser(self, sample_aqr_df: pd.DataFrame) -> AirQualityAnalyser:
        analyser = AirQualityAnalyser(sample_aqr_df)
        return analyser

    @pytest.fixture
    def aqi_analyser_sj(self, sample_aqr_df_sj: pd.DataFrame) -> AirQualityAnalyser:
        analyser = AirQualityAnalyser(sample_aqr_df_sj)
        return analyser

    def test_filter_by_city(self, aqi_analyser: AirQualityAnalyser):

        filtered = aqi_analyser.filter_by_city("Sarajevo")

        # Check we have a proper AQA object
        assert isinstance(filtered, AirQualityAnalyser)

        # Should have four rows returned
        assert filtered.df.shape[0] == 4

        # City should be Sarajevo in all cases, i.e. one unique value
        assert filtered.df["city"].nunique() == 1

    def test_filter_by_date_range(self, aqi_analyser: AirQualityAnalyser):

        # Filter with start & end dates
        filtered = aqi_analyser.filter_by_date_range(
            start_date="2026-03-27 09:00:00+00:00", end_date="2026-03-27 11:00:00+00:00"
        )
        assert isinstance(filtered, AirQualityAnalyser)  # Is it an AQA?
        assert filtered.df.shape[0] == 6  # Should have six records

        # Filter with just start date
        filtered = aqi_analyser.filter_by_date_range(start_date="")
        assert True  # What?

        # Filter with just end date
        filtered = aqi_analyser.filter_by_date_range(end_date="")
        assert True  # What?

        # Filter with no dates
        filtered = aqi_analyser.filter_by_date_range()
        assert True  # What?

    def test_get_aqi_by_date_range(self, aqi_analyser_sj: AirQualityAnalyser):

        filtered = aqi_analyser_sj.get_aqi_by_date_range(
            start_date=datetime(2026, 3, 27, 9, 0),
            end_date=datetime(2026, 3, 27, 11, 0),
        )

        assert filtered.shape[0] == 2
        assert (
            filtered[aqi_analyser_sj.timestamp_col]
            >= pd.Timestamp("2026-03-27T09:00:00", tz="Europe/Sarajevo")
        ).all()
        assert (
            filtered[aqi_analyser_sj.timestamp_col]
            <= pd.Timestamp("2026-03-27T11:00:00", tz="Europe/Sarajevo")
        ).all()

    def test_plot_line_chart(self, aqi_analyser_sj: AirQualityAnalyser):

        df = aqi_analyser_sj.df[["city", aqi_analyser_sj.timestamp_col, "aqi"]]
        fig = aqi_analyser_sj.plot_line_chart(df, aqi_analyser_sj.timestamp_col, "aqi")

        assert isinstance(fig, Figure)
