from config import Config
from client import AirQualityClient
from storage import CSVStorage
import json

def run_app():
    # Load configuration
    config = Config()
    
    # Initialize API client
    client = AirQualityClient(config.IQAIR_API_KEY, config.IQAIR_BASE_URL)

    # Get list of countries
    #countries = client.get_all_countries()
    #print(f'\n\nCountries with available data:')
    #print(json.dumps(countries, indent=4))

    # Get list of states for a specific country
    #states = client.get_all_states('Bosnia Herzegovina')
    #print(f'\n\nStates in Bosnia Herzegovina with available data:')
    #print(json.dumps(states, indent=4))

    # Get list of cities for a specific country and state
    #cities = client.get_all_cities('Bosnia Herzegovina', 'Federation of B&H')
    #print(f'\n\nCities in Federation of Bosnia and Herzegovina with available data:')
    #print(json.dumps(cities, indent=4))

    # Get nearest city based on IP geolocation
    #nearest_city = client.get_nearest_city()
    #print(f'\n\nNearest city based on IP geolocation:')
    #print(json.dumps(nearest_city, indent=4))

    # Get nearest city based on supplied latitude and longitude
    #nearest_city_by_coords = client.get_nearest_city(lat=43.85, lon=18.38)
    #print(f'\n\nNearest city based on supplied coordinates (lat=43.85, lon=18.38):')
    #print(json.dumps(nearest_city_by_coords, indent=4))

    city_data = client.get_city_data('Sarajevo','Federation of B&H','Bosnia Herzegovina')
    print(f'\n\nAir quality data for Sarajevo:')
    print(json.dumps(city_data, indent=4))

    # Initialize storage (using CSV as an example)
    storage = CSVStorage()

    storage.save('Hello')  # Replace None with actual AirQualityReading object



def main():
    print('Starting Air Quality Monitor Application...')
    run_app()


if __name__ == "__main__":
    main()