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
class City:
    # A dataclass to represent a city with its name and location details
    city: str
    state: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None



