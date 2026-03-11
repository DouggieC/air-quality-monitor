import logging
from datetime import datetime
from .models import AirQualityReading

class ResponseParser:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Creating ResponseParser object')

    def _parse_timestamp(self, ts):
        self.logger.debug('Executing _parse_timestamp')

        # Force timestamps into datetime objects
        if ts is None:
            self.logger.debug('Timestamp not set')
            return datetime.fromtimestamp(0)

        # Already a number
        if isinstance(ts, (int, float)):
            self.logger.debug('Timestamp is a number')
            return datetime.fromtimestamp(ts)

        # Try to coerce numeric strings first
        if isinstance(ts, str):
            self.logger.debug('Timestamp is a string')
            if ts.isdigit():
                return datetime.fromtimestamp(int(ts))
            try:
                # ISO format, e.g. "2023-03-02T12:34:56.000Z" or similar
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Fallback
        self.logger.debug('Can\'t figure it out. Returning best effort')
        return datetime.fromtimestamp(0)
    
    def parse(self, raw_data: dict) -> AirQualityReading:
        self.logger.debug('Executing parse')

        # Get at nested values
        pollution = raw_data.get('current', {}).get('pollution', {})
        weather = raw_data.get('current', {}).get('weather', {})

        
        aqr = AirQualityReading(
            city=raw_data.get('city'),
            state=raw_data.get('state'),
            country=raw_data.get('country'),
            latitude=raw_data.get('latitude'),
            longitude=raw_data.get('longitude'),
            aqi=pollution.get('aqius'),
            main_pollutant=pollution.get('mainus'),
            pollutant_timestamp=self._parse_timestamp(pollution.get('ts')),
            temperature=weather.get('tp'),
            humidity=weather.get('hu'),
            pressure=weather.get('pr'),
            wind_speed=weather.get('ws'),
            wind_direction=weather.get('wd'),
            heat_index=weather.get('hi'),
            weather_timestamp=self._parse_timestamp(weather.get('ts')),
            collected_at=datetime.now()
        )
        self.logger.debug(f'AirQualityReading:\t{aqr}')
        return aqr