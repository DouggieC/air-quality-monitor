import requests
import logging
from .exceptions import *
from dataclasses import dataclass
from .models import City
#from datetime import datetime
#import json

class AirQualityClient:
    # A client class to interact with the IQAir Air Quality API
    def __init__(self, api_key, base_url):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f'Creating object')
        self.api_key = api_key
        self.base_url = base_url
        
    def get_all_countries(self):
        # Gets list of all countries with available data
        self.logger.debug('Executing method')

        params = {
            'key': self.api_key
        }
        self.logger.debug(f'Parameters:\t{params}')

        url = f'{self.base_url}countries'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)
        
        data = response.json()
        self.logger.debug(f'Data received:\t{data}')
        return data.get('data', [])
    
    def get_all_states(self, country):
        # Gets list of all states for the supplied country
        self.logger.debug('Executing method')

        params = {
            'country': country,
            'key': self.api_key
        }
        self.logger.debug(f'Parameters:\t{params}')

        url = f'{self.base_url}states'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()
        self.logger.debug(f'Data received:\t{data}')
        return data.get('data', [])
    
    def get_all_cities(self, country, state):
        # Gets list of all cities for the supplied country and state
        self.logger.debug('Executing method')

        params = {
            'country': country,
            'state': state,
            'key': self.api_key
        }
        self.logger.debug(f'Parameters:\t{params}')

        url = f'{self.base_url}cities'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()
        self.logger.debug(f'Data received:\t{data}')
        return data.get('data', [])
    
    def get_nearest_city(self, lat=None, lon=None):
        # Gets nearest city based on supplied latitude and longitude, 
        # or based on IP geolocation if lat/lon not supplied
        self.logger.debug('Executing method')

        params = {
            'lat': lat,
            'lon': lon,
            'key': self.api_key
        }
        self.logger.debug(f'Parameters:\t{params}')
    
        url = f'{self.base_url}nearest_city'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()
        self.logger.debug(f'Data received:\t{data}')
        return data.get('data', {})
    
    def get_city_data(self, city: City) -> dict:
        # Gets air quality data for the supplied city, state, and country
        self.logger.debug('Executing method')

        params = {
            'city': city.city,
            'state': city.state,
            'country': city.country,
            'key': self.api_key
        }
        self.logger.debug(f'Parameters:\t{params}')
    
        url = f'{self.base_url}city'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()
        self.logger.debug(f'Data received:\t{data}')
        if data.get('status') != 'success':
            raise APIError(f"IQAir API returned status '{data.get('status')}' for city {city.city}")

        return response.json()

class WeatherClient:
    # A client to interact with the OpenWeatherMap API
    def __init__(self, api_key, owm_oc_base_url, owm_geo_base_url):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f'Creating object')
        self.api_key = api_key
        self.oc_base_url = owm_oc_base_url
        self.geo_base_url = owm_geo_base_url
    
    def get_coordinates(self, city: City, limit=None) -> dict:
        # Get the latitude and longitude of a city
        self.logger.debug('Executing method')

        params = {
            'q': city.city,
            'appid': self.api_key,
            'limit': limit
        }
        self.logger.debug(f'Parameters:\t{params}')

        url = f'{self.geo_base_url}direct'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()[0]
        self.logger.debug(f'Data received:\t{data}')

        if data.get('code') is not None or data.get('cod') is not None:
            raise APIError(f"OWM API failed for city {city.city}: error code {data.get('code')}: {data.get('message')}")
        
        return data
    
    def get_location(self, lat, lon, limit=None):
        # Get the closest named location to the given coordinates
        self.logger.debug('Executing method')

        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'limit': limit
        }
        self.logger.debug(f'Parameters:\t{params}')

        url = f'{self.geo_base_url}reverse'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()
        self.logger.debug(f'Data received:\t{data}')


        if data.get('code') is not None or data.get('cod') is not None:
            raise APIError(f"OWM API failed for coords [{lat},{lon}]: error code {data.get('code')}: {data.get('message')}")
        
        return data
    
    def get_current_weather(self, *, lat=None, lon=None, city: City | None = None):
        # Get the full current weather data for the specified location
        self.logger.debug('Executing method')

        # Method requires either lat & lon or city
        if city is None and lat is None and lon is None:
            raise ValueError('Must specify either city or lat/lon coordinates')
        if (lat is None and lon is not None) or (lat is not None and lon is None):
            raise ValueError('Both lat and lon must be provided')
        if city is not None and (lat is not None or lon is not None):
            raise ValueError('Only one of city or lat/lon must be specified')
        
        if city:
            self.logger.debug(f'City name supplied. Getting coordinates...')
            coords = self.get_coordinates(city)
            lat = coords.get('lat')
            lon = coords.get('lon')
            self.logger.debug(f'Coords for {city}:\t[{lat},{lon}]')
        
        params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'minutely,hourly,daily,alerts',
            'units': 'metric',
            'appid': self.api_key
        }
        self.logger.debug(f'Parameters:\t{params}')

        url = f'{self.oc_base_url}'
        self.logger.debug(f'URL:\t{url}')
        response = requests.get(url, params=params)

        data = response.json()
        self.logger.debug(f'Data received:\t{data}')
        if data.get('code') is not None or data.get('cod') is not None:
            raise APIError(f"OWM API failed for coords [{lat},{lon}]: error code {data.get('code')}: {data.get('message')}")
        
        return data 







