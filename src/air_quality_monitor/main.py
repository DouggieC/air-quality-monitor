import logging
from .config import Config
from .client import AirQualityClient
from .storage import JSONStorage, CSVStorage
from .parser import ResponseParser
from .pipeline import PipelineRunner
from .logger import setup_logging

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
    #config = Config()
    
    # Ensure data & log directories exist
    #config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(__name__)
    logger.debug('Executing run_pipeline')

    client = AirQualityClient(Config.IQAIR_API_KEY, Config.IQAIR_BASE_URL)
    parser = ResponseParser()
    raw_storage = JSONStorage()
    parsed_storage = CSVStorage()

    cities = Config.load_cities()
    logger.debug(f'Cities:\t{cities}')

    runner = PipelineRunner(client, parser, raw_storage, parsed_storage, Config.DATA_DIR)
    runner.run(cities)




def main():
    
    # Start logging
    setup_logging(log_level=Config.LOG_LEVEL, log_dir=Config.LOG_DIR)
    logger = logging.getLogger(__name__)
    logger.info("Air Quality Monitor started")
            
    #run_app()
    run_pipeline()

    logger.info("Air Quality Monitor finished")


if __name__ == "__main__":
    main()