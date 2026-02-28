import requests

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
        return data.get('data', {})
    
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
        return data.get('data', {})
    



