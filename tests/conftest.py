from datetime import datetime

import pytest

from air_quality_monitor.models import AirQualityReading, City, WeatherReading


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
