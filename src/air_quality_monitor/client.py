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
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating AirQualityClient object')
        self.api_key = api_key
        self.base_url = base_url
        
    def get_all_countries(self):
        # Gets list of all countries with available data

        self.logger.debug("Executing get_all_countries")

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

        self.logger.debug('Executing get_all_states')

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
        self.logger.debug('Executing get_all_cities')

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
        self.logger.debug('Executing get_nearest_city')

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
        self.logger.debug('Executing get_city_data')

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
            raise APIError(f"API returned status '{data.get('status')}' for city {city.city}")

        return response.json()

        
    
