from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Reading:
    pass


@dataclass
class AirQualityReading(Reading):
    # A dataclass to represent a single air quality reading with all relevant fields
    city: str
    state: str
    country: str
    timezone: str
    latitude: float
    longitude: float
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
    collected_at: datetime  # Timestamp when this reading was collected from the API


@dataclass
class WeatherReading(Reading):
    # A dataclass to represent a single weather reading
    city: str
    state: str
    country: str
    timezone: str
    latitude: float
    longitude: float
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
    collected_at: datetime  # Timestamp when this reading was collected from the API


@dataclass
class WeatherAlert(Reading):
    # A dataclass to represent a severe weather alert
    sender_name: str  # Alert source. See https://openweathermap.org/api/one-call-3?collection=one_call_api_3.0#listsource
    event: str  # Alert event name
    start: datetime  # Start date & time (UTC timestamp)
    end: datetime  # End date & time (UTC timestamp)
    description: str  # Description of the alert
    tags: list[str]  # Type of severe weather


@dataclass
class City:
    # A dataclass to represent a city with its name and location details
    city: str
    state: str
    country: str
    timezone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
