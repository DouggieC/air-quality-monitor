import requests
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AirQualityReading:
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    aqi: int                # AQI based on US EPA standard
    main_pollutant: str     # Main pollutant contributing to the AQI
    pollutant_timestamp: datetime   # Timestamp of the pollutant measurement
    temperature: int        # Temperature in Celsius
    min_temperature: int    # Minimum temperature in the last 24 hours
    humidity: int           # Humidity percentage
    pressure: int           # Atmospheric pressure in hPa
    wind_speed: int         # Wind speed in m/s
    wind_direction: int     # Wind direction in degrees
    heat_index: int         # Apparent temperature in Celsius, calculated from temperature and relative humidity
    weather_timestamp: datetime     # Timestamp of the weather measurement
    collected_at: datetime  # Timestamp when this reading was collected from the API

class AirQualityClient:
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
        reading = self._parse_air_quality_data(data.get('data', {}))
        return reading
    
    def _parse_air_quality_data(self, data) -> AirQualityReading:
        # Parses the raw API response data into an AirQualityReading object
        return AirQualityReading(
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            aqi=data.get('aqi'),
            main_pollutant=data.get('main_pollutant'),
            pollutant_timestamp=datetime.fromtimestamp(data.get('pollutant_timestamp', 0)),
            temperature=data.get('temperature'),
            min_temperature=data.get('min_temperature'),
            humidity=data.get('humidity'),
            pressure=data.get('pressure'),
            wind_speed=data.get('wind_speed'),
            wind_direction=data.get('wind_direction'),
            heat_index=data.get('heat_index'),
            weather_timestamp=datetime.fromtimestamp(data.get('weather_timestamp', 0)),
            collected_at=datetime.now()
        )
    

