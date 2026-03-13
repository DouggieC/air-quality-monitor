from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AirQualityReading:
    # A dataclass to represent a single air quality reading with all relevant fields
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    aqi: int                # AQI based on US EPA standard
    main_pollutant: str     # Main pollutant contributing to the AQI
    pollutant_timestamp: datetime   # Timestamp of the pollutant measurement
    temperature: int        # Temperature in Celsius
    humidity: int           # Humidity percentage
    pressure: int           # Atmospheric pressure in hPa
    wind_speed: int         # Wind speed in m/s
    wind_direction: int     # Wind direction in degrees
    heat_index: int         # Apparent temperature in Celsius, calculated from temperature and relative humidity
    weather_timestamp: datetime     # Timestamp of the weather measurement
    collected_at: datetime  # Timestamp when this reading was collected from the API

@dataclass
class WeatherReading:
    # A dataclass to represent a single weather reading
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    timezone_offset: int    # Offset from UTC (seconds)
    dt_utc: int         # Observation time (UTC timestamp)
    dt_local: int       # Observation time (Local timestamp)
    sunrise_utc: int    # Sunrise time (UTC timestamp)
    sunrise_local: int  # Sunrise time (Local timestamp)
    sunset_utc: int     # Sunset time (UTC timestamp)
    sunset_local: int   # Sunset time (Local timestamp)
    temperature: float  # Temperature (C; default response is K but API calls request metric)
    feels_like: float   # Perceived temperature (C)
    pressure: int       # Atmospheric pressure at MSL, hPa
    humidity: int       # Humidity (%)
    dew_point: float    # Air temp at which water condenses and dew can form (C)
    uvi: float          # UV index
    clouds: int         # Cloudiness (%)
    visibility: int     # Average visibility (m, max 10km)
    wind_speed: float   # Wind speed (m/s)
    wind_direction: int # Wind direction (degrees)
    wind_gust: int      # Wind gust speed (m/s)
    rain: int           # Rainfall (mm/h)
    snow: int           # Snowfall (mm/h)
    conditions: str     # JSON string contining a list of weather condition dicts

@dataclass
class WeatherAlert:
    # A dataclass to represent a severe weather alert
    sender_name: str    # Alert source. See https://openweathermap.org/api/one-call-3?collection=one_call_api_3.0#listsource
    event: str          # Alert event name
    start: int          # Start date & time (UTC timestamp)
    end: int            # End date & time (UTC timestamp)
    description: str    # Description of the alert
    tags: list[str]     # Type of severe weather


@dataclass
class City:
    # A dataclass to represent a city with its name and location details
    city: str
    state: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None



