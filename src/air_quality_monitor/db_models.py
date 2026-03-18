from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    pass

class DBCity(Base):
    __tablename__ = 'city'

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

class DBAirQualityReading(Base):
    __tablename__ = 'air_quality_reading'

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey('city.id'))
    aqi: Mapped[int] = mapped_column(Integer)                # AQI based on US EPA standard
    main_pollutant: Mapped[str] = mapped_column(String(10))  # Main pollutant contributing to the AQI
    pollutant_timestamp: Mapped[datetime] = mapped_column(DateTime)   # Timestamp of the pollutant measurement
    temperature: Mapped[int] = mapped_column(Integer)        # Temperature in Celsius
    humidity: Mapped[int] = mapped_column(Integer)           # Humidity percentage
    pressure: Mapped[int] = mapped_column(Integer)           # Atmospheric pressure in hPa
    wind_speed: Mapped[float] = mapped_column(Float)         # Wind speed in m/s
    wind_direction: Mapped[int | None] = mapped_column(Integer, nullable=True) # Wind direction in degrees
    heat_index: Mapped[float | None] = mapped_column(Float, nullable=True) # Apparent temperature in Celsius, calculated from temperature and relative humidity
    weather_timestamp: Mapped[datetime] = mapped_column(DateTime)          # Timestamp of the weather measurement
    collected_at: Mapped[datetime] = mapped_column(DateTime) # Timestamp when this reading was collected from the API


class DBWeatherReading(Base):
    __tablename__ = 'weather_reading'

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey('city.id'))
    timezone: Mapped[str] = mapped_column(String(100))
    timezone_offset: Mapped[int] = mapped_column(Integer)          # Offset from UTC (seconds)
    dt_utc: Mapped[datetime] = mapped_column(DateTime)             # Observation time (UTC timestamp)
    dt_local: Mapped[datetime] = mapped_column(DateTime)           # Observation time (Local timestamp)
    sunrise_utc: Mapped[datetime] = mapped_column(DateTime)        # Sunrise time (UTC timestamp)
    sunrise_local: Mapped[datetime] = mapped_column(DateTime)      # Sunrise time (Local timestamp)
    sunset_utc: Mapped[datetime] = mapped_column(DateTime)         # Sunset time (UTC timestamp)
    sunset_local: Mapped[datetime] = mapped_column(DateTime)       # Sunset time (Local timestamp)
    temperature: Mapped[float] = mapped_column(Float)              # Temperature (C; default response is K but API calls request metric)
    feels_like: Mapped[float] = mapped_column(Float)               # Perceived temperature (C)
    pressure: Mapped[int] = mapped_column(Integer)                 # Atmospheric pressure at MSL, hPa
    humidity: Mapped[int] = mapped_column(Integer)                 # Humidity (%)
    dew_point: Mapped[float] = mapped_column(Float)                # Air temp at which water condenses and dew can form (C)
    uvi: Mapped[float] = mapped_column(Float)                      # UV index
    clouds: Mapped[int] = mapped_column(Integer)                   # Cloudiness (%)
    visibility: Mapped[int] = mapped_column(Integer)               # Average visibility (m, max 10km)
    wind_speed: Mapped[float] = mapped_column(Float)               # Wind speed (m/s)
    wind_direction: Mapped[int] = mapped_column(Integer)           # Wind direction (degrees)
    wind_gust: Mapped[float | None] = mapped_column(Float, nullable=True) # Wind gust speed (m/s)
    rain: Mapped[float | None] = mapped_column(Float, nullable=True)      # Rainfall (mm/h)
    snow: Mapped[float | None] = mapped_column(Float, nullable=True)      # Snowfall (mm/h)
    weather_main: Mapped[str] = mapped_column(String(100))         # The main weather (clouds, rain, sun, etc.)
    weather_desc: Mapped[str] = mapped_column(String(100))         # The weather description ('few clouds', etc.)
    collected_at: Mapped[datetime] = mapped_column(DateTime)       # Timestamp when this reading was collected from the API

