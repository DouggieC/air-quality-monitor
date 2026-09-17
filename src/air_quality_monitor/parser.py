import logging
from datetime import datetime, timezone

from .exceptions import ParseError
from .models import AirQualityReading, City, WeatherReading, HourlyForecast, DailyForecast


class ResponseParser:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")

    def _parse_timestamp(self, ts):
        self.logger.debug(f"Executing method (ts={ts})")

        # Force timestamps into datetime objects
        if ts is None:
            self.logger.debug("Timestamp not set")
            # return datetime.fromtimestamp(0, timezone.utc) # Return epoch time
            raise ParseError(f"Timestamp missing: {ts!r}")

        # Already a number
        if isinstance(ts, (int, float)):
            # Convert Unix timestamp to UTC-aware datetime
            self.logger.debug("Timestamp is a number")
            return datetime.fromtimestamp(ts, timezone.utc)

        # Try to coerce numeric strings first
        if isinstance(ts, str):
            self.logger.debug("Timestamp is a string")
            if ts.isdigit():
                return datetime.fromtimestamp(int(ts), timezone.utc)
            try:
                # ISO format, e.g. "2023-03-02T12:34:56.000Z" or similar
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    return dt.astimezone(timezone.utc)
                else:
                    return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        # Fallback
        # self.logger.debug("Can't figure it out. Returning best effort")
        # return datetime.fromtimestamp(0, timezone.utc) # Return epoch time
        self.logger.debug("Can't figure it out.")
        raise ParseError(f"Unrecognized timestamp: {ts!r}")


class AirQualityParser(ResponseParser):
    def parse(self, raw_data: dict, city: City) -> AirQualityReading:
        self.logger.debug("Executing method")
        self.logger.debug(f"Raw data received:\t{raw_data}")


        # Get at nested values
        pollution = raw_data.get("current", {}).get("pollution", {})
        weather = raw_data.get("current", {}).get("weather", {})

        aqr = AirQualityReading(
            city=city.city,
            state=city.state,
            country=city.country,
            timezone=city.timezone,
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
            collected_at=datetime.now(timezone.utc),
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
            timezone=city.timezone,
            latitude=raw_data.get("lat"),
            longitude=raw_data.get("lon"),
            dt=self._parse_timestamp(current.get("dt")),
            sunrise=self._parse_timestamp(current.get("sunrise")),
            sunset=self._parse_timestamp(current.get("sunset")),
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
            rain=current.get("rain", {}).get("1h", 0.0),
            snow=current.get("snow", {}).get("1h", 0.0),
            weather_main=current.get("weather", [{}])[0].get("main"),
            weather_desc=current.get("weather", [{}])[0].get("description"),
            collected_at=datetime.now(timezone.utc),
        )
        self.logger.debug(f"WeatherReading:\t{wr}")
        return wr

class HourlyForecastParser(ResponseParser):
    def parse(self, raw_data: dict, city: City) -> list[HourlyForecast]:
        self.logger.debug("Executing method")
        self.logger.debug(f"Raw data received:\t{raw_data}")

        # Get at nested values
        hourly = raw_data.get("hourly", [])
        self.logger.debug(f"Hourly data:\t{hourly}")
        lat=raw_data.get("lat")
        lon=raw_data.get("lon")
        coll_at=datetime.now(timezone.utc)

        hours = []
        for h in hourly:
            hr = HourlyForecast(
                city=city.city,
                state=city.state,
                country=city.country,
                timezone=city.timezone,
                latitude=lat,
                longitude=lon,
                forecast_for=self._parse_timestamp(h.get("dt")),
                temperature=h.get("temp"),
                feels_like=h.get("feels_like"),
                pressure=h.get("pressure"),
                humidity=h.get("humidity"),
                dew_point=h.get("dew_point"),
                uvi=h.get("uvi"),
                clouds=h.get("clouds"),
                visibility=h.get("visibility"),
                wind_speed=h.get("wind_speed"),
                wind_direction=h.get("wind_deg"),
                wind_gust=h.get("wind_gust"),
                pop=h.get("pop"),
                rain=h.get("rain", {}).get("1h", 0.0),
                snow=h.get("snow", {}).get("1h", 0.0),
                weather_main=h.get("weather", [{}])[0].get("main"),
                weather_desc=h.get("weather", [{}])[0].get("description"),
                collected_at=coll_at
            )
            self.logger.debug(f"HourlyForecast:\t{hr}")
            hours.append(hr)

        return hours

class DailyForecastParser(ResponseParser):
    def parse(self, raw_data: dict, city: City) -> list[DailyForecast]:
        self.logger.debug("Executing method")
        self.logger.debug(f"Raw data received:\t{raw_data}")

        # Get at nested values
        daily = raw_data.get("daily", [])
        self.logger.debug(f"Daily data:\t{daily}")
        lat=raw_data.get("lat")
        lon=raw_data.get("lon")
        coll_at=datetime.now(timezone.utc)

        days = []
        for d in daily:
            day = DailyForecast(
                city=city.city,
                state=city.state,
                country=city.country,
                timezone=city.timezone,
                latitude=lat,
                longitude=lon,
                forecast_for=self._parse_timestamp(d.get("dt")),
                sunrise=self._parse_timestamp(d.get("sunrise")),
                sunset=self._parse_timestamp(d.get("sunset")),
                temp_morn=d.get("temp", {}).get("morn"),
                temp_day=d.get("temp", {}).get("day"),
                temp_eve=d.get("temp", {}).get("eve"),
                temp_night=d.get("temp", {}).get("night"),
                temp_min=d.get("temp", {}).get("min"),
                temp_max=d.get("temp", {}).get("max"),
                feels_like_morn=d.get("feels_like", {}).get("morn"),
                feels_like_day=d.get("feels_like", {}).get("day"),
                feels_like_eve=d.get("feels_like", {}).get("eve"),
                feels_like_night=d.get("feels_like", {}).get("night"),
                pressure=d.get("pressure"),
                humidity=d.get("humidity"),
                dew_point=d.get("dew_point"),
                uvi=d.get("uvi"),
                clouds=d.get("clouds"),
                wind_speed=d.get("wind_speed"),
                wind_direction=d.get("wind_deg"),
                wind_gust=d.get("wind_gust"),
                pop=d.get("pop"),
                rain=d.get("rain", 0.0),
                snow=d.get("snow", 0.0),
                weather_main=d.get("weather", [{}])[0].get("main"),
                weather_desc=d.get("weather", [{}])[0].get("description"),
                collected_at=coll_at
            )
            self.logger.debug(f"DailyForecast:\t{day}")
            days.append(day)

        return days

