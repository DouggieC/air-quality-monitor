from .config import Config
from .client import AirQualityClient
from .storage import JSONStorage, CSVStorage
from .parser import ResponseParser
from .pipeline import PipelineRunner
from .models import  City

def run_app():
    # Load configuration
    config = Config()

    # Ensure data directory exists
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize API client
    client = AirQualityClient(config.IQAIR_API_KEY, config.IQAIR_BASE_URL)

    #print(client.get_all_countries())
    print(client.get_all_states('Switzerland'))
    cities = client.get_all_cities('Switzerland', 'Geneva')
    for city in cities:
        print(f'{city}')

    '''city = 'Sarajevo'
    state = 'Federation of B&H'
    country = 'Bosnia Herzegovina'
    city_data = client.get_city_data(city, state, country)
    print(f'\n\nAir quality data for {city}:')
    #print(json.dumps(city_data, indent=4))
    print(city_data)

    # Store raw JSON data to provide history
    raw_storage = JSONStorage()
    base_filename = f'{config.DATA_DIR}/{city}_raw_history'
    raw_storage.save(city_data, base_filename)'''

def run_pipeline():

    # Load the config
    config = Config()

    # Ensure data directory exists
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    client = AirQualityClient(config.IQAIR_API_KEY, config.IQAIR_BASE_URL)
    parser = ResponseParser()
    raw_storage = JSONStorage()
    parsed_storage = CSVStorage()

    cities = [
        City(city='Sarajevo', state='Federation of B&H', country='Bosnia Herzegovina'),
        City(city='London', state='England', country='United Kingdom'),
        City(city='Founex', state='Vaud', country='Switzerland'),
        City(city='Le Grand-Saconnex', state='Geneva', country='Switzerland'),
    ]
    runner = PipelineRunner(client, parser, raw_storage, parsed_storage, config.DATA_DIR)
    runner.run(cities)




def main():
    print('Starting Air Quality Monitor Application...')
    run_app()
    #run_pipeline()


if __name__ == "__main__":
    main()