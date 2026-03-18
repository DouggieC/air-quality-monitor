import logging
from datetime import datetime

from .models import AirQualityReading, City, WeatherReading


class ResponseParser:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")

    def _parse_timestamp(self, ts):
        self.logger.debug(f"Executing method (ts={ts})")

        # Force timestamps into datetime objects
        if ts is None:
            self.logger.debug("Timestamp not set")
            return datetime.fromtimestamp(0)

        # Already a number
        if isinstance(ts, (int, float)):
            self.logger.debug("Timestamp is a number")
            return datetime.fromtimestamp(ts)

        # Try to coerce numeric strings first
        if isinstance(ts, str):
            self.logger.debug("Timestamp is a string")
            if ts.isdigit():
                return datetime.fromtimestamp(int(ts))
            try:
                # ISO format, e.g. "2023-03-02T12:34:56.000Z" or similar
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Fallback
        self.logger.debug("Can't figure it out. Returning best effort")
        return datetime.fromtimestamp(0)


class AirQualityParser(ResponseParser):
    def parse(self, raw_data: dict, city: City) -> AirQualityReading:
        self.logger.debug("Executing method")

        # Get at nested values
        pollution = raw_data.get("current", {}).get("pollution", {})
        weather = raw_data.get("current", {}).get("weather", {})

        aqr = AirQualityReading(
            city=city.city,
            state=city.state,
            country=city.country,
            latitude=raw_data.get("latitude"),
            longitude=raw_data.get("longitude"),
            aqi=pollution.get("aqius"),
            main_pollutant=pollution.get("mainus"),
            pollutant_timestamp=self._parse_timestamp(pollution.get("ts")),
            temperature=weather.get("tp"),
            humidity=weather.get("hu"),
            pressure=weather.get("pr"),
            wind_speed=weather.get("ws"),
            wind_direction=weather.get("wd"),
            heat_index=weather.get("hi"),
            weather_timestamp=self._parse_timestamp(weather.get("ts")),
            collected_at=datetime.now(),
        )
        self.logger.debug(f"AirQualityReading:\t{aqr}")
        return aqr


class WeatherParser(ResponseParser):
    def parse(self, raw_data: dict, city: City) -> WeatherReading:
        self.logger.debug("Executing method")
        self.logger.debug(f"Raw data received:\t{raw_data}")

        # Get at nested values
        current = raw_data.get("current", {})
        self.logger.debug(f"Current data:\t{current}")
        timezone_offset = raw_data.get("timezone_offset")
        self.logger.debug(f"TZ offset:\t{timezone_offset}")

        wr = WeatherReading(
            city=city.city,
            state=city.state,
            country=city.country,
            latitude=raw_data.get("lat"),
            longitude=raw_data.get("lon"),
            timezone=raw_data.get("timezone"),
            timezone_offset=timezone_offset,
            dt_utc=self._parse_timestamp(current.get("dt")),
            dt_local=self._parse_timestamp(current.get("dt") + timezone_offset),
            sunrise_utc=self._parse_timestamp(current.get("sunrise")),
            sunrise_local=self._parse_timestamp(
                current.get("sunrise") + timezone_offset
            ),
            sunset_utc=self._parse_timestamp(current.get("sunset")),
            sunset_local=self._parse_timestamp(current.get("sunset") + timezone_offset),
            temperature=current.get("temp"),
            feels_like=current.get("feels_like"),
            pressure=current.get("pressure"),
            humidity=current.get("humidity"),
            dew_point=current.get("dew_point"),
            uvi=current.get("uvi"),
            clouds=current.get("clouds"),
            visibility=current.get("visibility"),
            wind_speed=current.get("wind_speed"),
            wind_gust=current.get("wind_gust"),
            wind_direction=current.get("wind_deg"),
            rain=current.get("rain", {}).get("1h"),
            snow=current.get("snow", {}).get("1h"),
            weather_main=current.get("weather", [{}])[0].get("main"),
            weather_desc=current.get("weather", [{}])[0].get("description"),
            collected_at=datetime.now(),
        )
        self.logger.debug(f"WeatherReading:\t{wr}")
        return wr
