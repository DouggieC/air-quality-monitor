"""
Domain models for AQI and weather data.

Dataclass definitions for readings, forecasts, predictions, and cities.
Used for type-safe data transfer between API clients, parsers, and storage.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reading:
    """Base class for all timestamped readings with location data."""
    city: str
    state: str
    country: str
    timezone: str
    latitude: float
    longitude: float
    collected_at: datetime  # Timestamp when this reading was collected from the API


@dataclass
class AirQualityReading(Reading):
    """AQI reading from IQAir with pollutant and basic weather data."""
    aqi: int  # AQI based on US EPA standard
    main_pollutant: str  # Main pollutant contributing to the AQI
    pollutant_timestamp: datetime  # Timestamp of the pollutant measurement
    temperature: int  # Temperature in Celsius
    humidity: int  # Humidity percentage
    pressure: int  # Atmospheric pressure in hPa
    wind_speed: float  # Wind speed in m/s
    wind_direction: int  # Wind direction in degrees
    heat_index: int  # Apparent temperature in Celsius, calculated from temperature and relative humidity
    weather_timestamp: datetime  # Timestamp of the weather measurement


@dataclass
class WeatherReading(Reading):
    """Current weather observation from OpenWeatherMap."""
    dt: datetime  # Observation time (UTC timestamp)
    sunrise: datetime  # Sunrise time (UTC timestamp)
    sunset: datetime  # Sunset time (UTC timestamp)
    temperature: float  # Temperature (C; default is K but API calls request metric)
    feels_like: float  # Perceived temperature (C)
    pressure: int  # Atmospheric pressure at MSL, hPa
    humidity: int  # Humidity (%)
    dew_point: float  # Air temp at which water condenses and dew can form (C)
    uvi: float  # UV index
    clouds: int  # Cloudiness (%)
    visibility: int  # Average visibility (m, max 10km)
    wind_speed: float  # Wind speed (m/s)
    wind_direction: int  # Wind direction (degrees)
    wind_gust: float  # Wind gust speed (m/s)
    rain: float  # Rainfall (mm/h)
    snow: float  # Snowfall (mm/h)
    weather_main: str  # The main weather (clouds, rain, sun, etc.)
    weather_desc: str  # The weather description ('few clouds', etc.)


@dataclass
class WeatherAlert(Reading):
    """Severe weather alert from OpenWeatherMap (not currently used)."""
    sender_name: str  # Alert source. See https://openweathermap.org/api/one-call-3?collection=one_call_api_3.0#listsource
    event: str  # Alert event name
    start: datetime  # Start date & time (UTC timestamp)
    end: datetime  # End date & time (UTC timestamp)
    description: str  # Description of the alert
    tags: list[str]  # Type of severe weather


@dataclass
class Forecast(Reading):
    """Base class for forecast data with target timestamp."""
    forecast_for: datetime  # Timestamp when the forecast is for


@dataclass
class HourlyForecast(Forecast):
    """Hourly weather forecast (48 hours) from OpenWeatherMap."""
    temperature: float  # Temperature (C; default is K but API calls request metric)
    feels_like: float  # Perceived temperature (C)
    pressure: int  # Atmospheric pressure at MSL, hPa
    humidity: int  # Humidity (%)
    dew_point: float  # Air temp at which water condenses and dew can form (C)
    uvi: float  # UV index
    clouds: int  # Cloudiness (%)
    visibility: int  # Average visibility (m, max 10km)
    wind_speed: float  # Wind speed (m/s)
    wind_direction: int  # Wind direction (degrees)
    wind_gust: float  # Wind gust speed (m/s)
    pop: float  # Probability of precipitation (0-1)
    rain: float  # Rainfall (mm/h)
    snow: float  # Snowfall (mm/h)
    weather_main: str  # The main weather (clouds, rain, sun, etc.)
    weather_desc: str  # The weather description ('few clouds', etc.)


@dataclass
class DailyForecast(Forecast):
    """Daily weather forecast (8 days) from OpenWeatherMap."""
    sunrise: datetime  # Sunrise time (UTC timestamp)
    sunset: datetime  # Sunset time (UTC timestamp)
    temp_morn: float  # Morning temperature (C; default is K but API calls request metric)
    temp_day: float  # Day temperature (C; default is K but API calls request metric)
    temp_eve: float  # Evening temperature (C; default is K but API calls request metric)
    temp_night: float  # Night temperature (C; default is K but API calls request metric)
    temp_min: float  # Min daily temperature (C; default is K but API calls request metric)
    temp_max: float  # Max daily temperature (C; default is K but API calls request metric)
    feels_like_morn: float  # Perceived morning temperature (C)
    feels_like_day: float  # Perceived  day temperature (C)
    feels_like_eve: float  # Perceived temperature (C)
    feels_like_night: float  # Perceived temperature (C)
    pressure: int  # Atmospheric pressure at MSL, hPa
    humidity: int  # Humidity (%)
    dew_point: float  # Air temp at which water condenses and dew can form (C)
    uvi: float  # UV index
    clouds: int  # Cloudiness (%)
    wind_speed: float  # Wind speed (m/s)
    wind_direction: int  # Wind direction (degrees)
    wind_gust: float  # Wind gust speed (m/s)
    pop: float  # Probability of precipitation (0-1)
    rain: float  # Rainfall (mm/h)
    snow: float  # Snowfall (mm/h)
    weather_main: str  # The main weather (clouds, rain, sun, etc.)
    weather_desc: str  # The weather description ('few clouds', etc.)


@dataclass
class City:
    """City configuration with location and timezone for data collection."""
    city: str
    state: str
    country: str
    timezone: str
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class Prediction(Reading):
    """Model-generated AQI prediction for a specific horizon."""
    forecast_for: datetime  # Timestamp when the prediction is for
    predicted_aqi: int  # Predicted AQI
    model_name: str  # Name of the model used (e.g. "lightgbm_short")
    horizon: int  # Prediction horizon in hours
