from dataclasses import asdict
from datetime import datetime, timedelta

import pandas as pd
import pytest

from air_quality_monitor.models import AirQualityReading, City, HourlyForecast, WeatherReading


@pytest.fixture
def sample_city() -> City:
    return City(
        city="Sarajevo",
        state="Federation of B&H",
        country="Bosnia Herzegovina",
        timezone="Europe/Sarajevo",
        latitude=43.8519774,
        longitude=18.3866868,
    )


@pytest.fixture
def sample_aqr() -> AirQualityReading:
    return AirQualityReading(
        city="Sarajevo",
        state="Federation of B&H",
        country="Bosnia Herzegovina",
        timezone="Europe/Sarajevo",
        latitude=43.8519774,
        longitude=18.3866868,
        aqi=63,
        main_pollutant="p2",
        pollutant_timestamp=datetime.fromisoformat("2026-03-19 16:00:00+00:00"),
        temperature=7,
        humidity=47,
        pressure=1016,
        wind_speed=4.17,
        wind_direction=60,
        heat_index=5,
        weather_timestamp=datetime.fromisoformat("2026-03-19 16:00:00+00:00"),
        collected_at=datetime.fromisoformat("2026-03-19 17:10:42.923474"),
    )


@pytest.fixture
def sample_wr() -> WeatherReading:
    return WeatherReading(
        city="Sarajevo",
        state="Federation of B&H",
        country="Bosnia Herzegovina",
        latitude=43.8519774,
        longitude=18.3866868,
        timezone="Europe/Sarajevo",
        timezone_offset=3600,
        dt_utc=datetime.fromisoformat("2026-03-20 21:33:45"),
        dt_local=datetime.fromisoformat("2026-03-20 22:33:45"),
        sunrise_utc=datetime.fromisoformat("2026-03-20 05:50:09"),
        sunrise_local=datetime.fromisoformat("2026-03-20 06:50:09"),
        sunset_utc=datetime.fromisoformat("2026-03-20 18:00:20"),
        sunset_local=datetime.fromisoformat("2026-03-20 19:00:20"),
        temperature=4.36,
        feels_like=2.08,
        pressure=1021,
        humidity=72,
        dew_point=-0.21,
        uvi=0,
        clouds=0,
        visibility=10000,
        wind_speed=2.57,
        wind_deg=210,
        wind_gust=6.83,
        rain=2.47,
        snow=4.28,
        weather_main="Clear",
        weather_desc="clear sky",
        collected_at=datetime.fromisoformat("2026-03-20 21:33:45.862527"),
    )


@pytest.fixture
def sample_hf() -> HourlyForecast:
    return HourlyForecast(
        city="Sarajevo",
        state="Federation of B&H",
        country="Bosnia Herzegovina",
        timezone="Europe/Sarajevo",
        latitude=43.8519774,
        longitude=18.3866868,
        forecast_for=datetime.fromisoformat("2026-03-20 21:00:00"),
        temperature=4.36,
        feels_like=2.08,
        pressure=1021,
        humidity=72,
        dew_point=-0.21,
        uvi=0,
        clouds=0,
        visibility=10000,
        wind_speed=2.57,
        wind_direction=210,
        wind_gust=6.83,
        pop=0.37,
        rain=2.47,
        snow=4.28,
        weather_main="Clear",
        weather_desc="clear sky",
        collected_at=datetime.fromisoformat("2026-03-20 21:33:45.862527"),
    )


@pytest.fixture
def sample_aqi_df(sample_aqr) -> pd.DataFrame:
    base_time = datetime(2026, 3, 20, 21, 33, 46)  # noqa: DTZ001
    rows = []
    for hour in range(72):
        for city in ["Sarajevo", "London"]:
            row = asdict(sample_aqr)
            row["id_aqi"] = 0
            row["city"] = city
            row["pollutant_timestamp"] = base_time + timedelta(hours=hour)
            row["aqi"] = hour + (10 if city == "London" else 0)
            rows.append(row)

    return pd.DataFrame(rows)


@pytest.fixture
def sample_hourly_df(sample_hf) -> pd.DataFrame:
    base_time = datetime(2026, 3, 20, 21, 33, 46)  # noqa: DTZ001
    horizons = [0, 1, 2, 4, 8, 12, 24, 48]
    rows = []

    for hour in range(72):
        collected_at = base_time + timedelta(hours=hour)
        for city in ["Sarajevo", "London"]:
            for h in horizons:
                row = asdict(sample_hf)
                row["id_we"] = 0
                row["city"] = city
                row["collected_at"] = collected_at
                row["forecast_for"] = collected_at + timedelta(hours=h)
                rows.append(row)

    return pd.DataFrame(rows)


class MockStorage:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def read(self) -> pd.DataFrame:
        return self.df
