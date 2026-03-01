import requests
from dataclasses import dataclass
from datetime import datetime
import json

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

class AirQualityClient:
    # A client class to interact with the IQAir Air Quality API
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
    
    def fetch_air_quality_data(self):
        print(f'Fetching air quality data from {self.base_url} with API key {self.api_key}')
        # TODO Implement the actual API call logic here using requests
    
    def get_all_countries(self):
        # Gets list of all countries with available data

        params = {
            'key': self.api_key
        }

        url = f'{self.base_url}countries'
        response = requests.get(url, params=params)
        
        data = response.json()
        return data.get('data', [])
    
    def get_all_states(self, country):
        # Gets list of all states for the supplied country

        params = {
            'country': country,
            'key': self.api_key
        }

        url = f'{self.base_url}states'
        response = requests.get(url, params=params)

        data = response.json()
        return data.get('data', [])
    
    def get_all_cities(self, country, state):
        # Gets list of all cities for the supplied country and state

        params = {
            'country': country,
            'state': state,
            'key': self.api_key
        }

        url = f'{self.base_url}cities'
        print(f'Fetching cities for country={country}, state={state} from {url}')

        response = requests.get(url, params=params)

        data = response.json()
        return data.get('data', [])
    
    def get_nearest_city(self, lat=None, lon=None):
        # Gets nearest city based on supplied latitude and longitude, 
        # or based on IP geolocation if lat/lon not supplied

        params = {
            'lat': lat,
            'lon': lon,
            'key': self.api_key
        }
    
        url = f'{self.base_url}nearest_city'
        response = requests.get(url, params=params)
        data = response.json()
        reading = self._parse_air_quality_data(data.get('data', {}))
        return reading
    
    def get_city_data(self, city, state, country):
        # Gets air quality data for the supplied city, state, and country

        params = {
            'city': city,
            'state': state,
            'country': country,
            'key': self.api_key
        }

        url = f'{self.base_url}city'
        response = requests.get(url, params=params)
        data = response.json()
        print(f'API response for city data (JSON dump): {json.dumps(data, indent=2)}')
        reading = self._parse_air_quality_data(data.get('data', {}))
        print(f'Parsed AirQualityReading: {reading}')
        return reading
    
    def _parse_timestamp(self, ts):
        # Force timestamps into datetime objects
        if ts is None:
            return datetime.fromtimestamp(0)

        # Already a number
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts)

        # Try to coerce numeric strings first
        if isinstance(ts, str):
            if ts.isdigit():
                return datetime.fromtimestamp(int(ts))
            try:
                # ISO format, e.g. "2023-03-02T12:34:56.000Z" or similar
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Fallback
        return datetime.fromtimestamp(0)

    def _parse_air_quality_data(self, data) -> AirQualityReading:
        # Parses the raw API response data into an AirQualityReading object
        print(f'Parsing air quality data: {data}')
        print(f'city:\t{data.get("city")}')
        print(f'current:\t{data.get("current")}')
        print(f'aqi:\t{data.get("current", {}).get("pollution", {}).get("aqius")}')

        pollution = data.get('current', {}).get('pollution', {})
        weather = data.get('current', {}).get('weather', {})

        aqr = AirQualityReading(
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
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
        print(f'Created AirQualityReading: {aqr}')
        return aqr
    

