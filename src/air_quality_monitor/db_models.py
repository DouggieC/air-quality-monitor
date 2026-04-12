from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DBCity(Base):
    __tablename__ = "city"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(50))


class DBAirQualityReading(Base):
    __tablename__ = "air_quality_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    aqi: Mapped[int] = mapped_column(Integer)  # AQI based on US EPA standard
    main_pollutant: Mapped[str] = mapped_column(String(10))  # Main pollutant contributing to the AQI
    pollutant_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # Pollutant timestamp
    temperature: Mapped[int] = mapped_column(Integer)  # Temperature in Celsius
    humidity: Mapped[int] = mapped_column(Integer)  # Humidity percentage
    pressure: Mapped[int] = mapped_column(Integer)  # Atmospheric pressure in hPa
    wind_speed: Mapped[float] = mapped_column(Float)  # Wind speed in m/s
    wind_direction: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Wind direction in degrees
    heat_index: Mapped[float | None] = mapped_column(Float, nullable=True)  # Apparent temperature (C)
    weather_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # Weather reading timestamp
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # API collection timestamp


class DBWeatherReading(Base):
    __tablename__ = "weather_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    dt: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # UTC Observation time
    sunrise: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # Sunrise time (UTC timestamp)
    sunset: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # Sunset time (UTC timestamp)
    temperature: Mapped[float] = mapped_column(Float)  # Temperature (C; default K but API calls request C)
    feels_like: Mapped[float] = mapped_column(Float)  # Perceived temperature (C)
    pressure: Mapped[int] = mapped_column(Integer)  # Atmospheric pressure at MSL, hPa
    humidity: Mapped[int] = mapped_column(Integer)  # Humidity (%)
    dew_point: Mapped[float] = mapped_column(Float)  # Air temp at which water condenses and dew can form (C)
    uvi: Mapped[float] = mapped_column(Float)  # UV index
    clouds: Mapped[int] = mapped_column(Integer)  # Cloudiness (%)
    visibility: Mapped[int] = mapped_column(Integer, nullable=True)  # Average visibility (m, max 10km)
    wind_speed: Mapped[float] = mapped_column(Float)  # Wind speed (m/s)
    wind_direction: Mapped[int] = mapped_column(Integer)  # Wind direction (degrees)
    wind_gust: Mapped[float | None] = mapped_column(Float, nullable=True)  # Wind gust speed (m/s)
    rain: Mapped[float | None] = mapped_column(Float, nullable=True)  # Rainfall (mm/h)
    snow: Mapped[float | None] = mapped_column(Float, nullable=True)  # Snowfall (mm/h)
    weather_main: Mapped[str] = mapped_column(String(100))  # The main weather (clouds, rain, sun, etc.)
    weather_desc: Mapped[str] = mapped_column(String(100))  # The weather description ('few clouds', etc.)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # API collection timestamp
