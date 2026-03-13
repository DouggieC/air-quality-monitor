import logging
from .config import Config
from .client import AirQualityClient, WeatherClient
from .storage import JSONStorage, CSVStorage
from .parser import AirQualityParser, WeatherParser
from .pipeline import PipelineRunner
from .logger import setup_logging

def run_app():
    logger = logging.getLogger(__name__)
    logger.debug('Executing method')

    # Ensure data directory exists
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize API clients
    aqc = AirQualityClient(Config.IQAIR_API_KEY, Config.IQAIR_BASE_URL)
    wc = WeatherClient(Config.OWM_API_KEY, Config.OWM_ONECALL_BASE_URL, Config.OWM_GEO_BASE_URL)

    # Get coordinates for Sarajevo
    cities = Config.load_cities()
    logger.debug(f'Cities:\t{cities}')

    for city in cities:
        #logger.debug(f'Getting coordinates for {city.city}')
        #coord_data = wc.get_coordinates(city)
        #lat = coord_data.get('lat')
        #lon = coord_data.get('lon')
        logger.debug(f'Getting weather data for {city}')
        weather_data = wc.get_current_weather(city=city)
        #logger.debug(f'Getting AQI data for {city.city}')
        #aqi_data = aqc.get_city_data(city)
        
        '''
        # Get weather for Sarajevo by coords
        print('Getting weather data')
        weather_data = wc.get_current_weather(43.8563, 18.4131)
        #print(weather_data)
        '''
    '''
    #print(aqc.get_all_countries())
    print(aqc.get_all_states('Switzerland'))
    cities = aqc.get_all_cities('Switzerland', 'Geneva')
    for city in cities:
        print(f'{city}')
    '''
    
    '''city = 'Sarajevo'
    state = 'Federation of B&H'
    country = 'Bosnia Herzegovina'
    city_data = aqc.get_city_data(city, state, country)
    print(f'\n\nAir quality data for {city}:')
    #print(json.dumps(city_data, indent=4))
    print(city_data)

    # Store raw JSON data to provide history
    raw_storage = JSONStorage()
    base_filename = f'{config.DATA_DIR}/{city}_raw_history'
    raw_storage.save(city_data, base_filename)
    '''

def run_pipeline():

    logger = logging.getLogger(__name__)
    logger.debug('Executing method')

    aqc = AirQualityClient(Config.IQAIR_API_KEY, Config.IQAIR_BASE_URL)
    aq_parser = AirQualityParser()
    we_parser = WeatherParser()
    raw_storage = JSONStorage()
    parsed_storage = CSVStorage()

    cities = Config.load_cities()
    logger.debug(f'Cities:\t{cities}')

    runner = PipelineRunner(aqc, aq_parser, we_parser, raw_storage, parsed_storage, Config.DATA_DIR)
    runner.run(cities)




def main():
    
    # Start logging
    setup_logging(log_level=Config.LOG_LEVEL, log_dir=Config.LOG_DIR)
    logger = logging.getLogger(__name__)
    logger.info("Air Quality Monitor started")
    logger.debug(f'Environment variables:')
    logger.debug(f'IQAIR_API_KEY:\t{Config.IQAIR_API_KEY}')
    logger.debug(f'IQAIR_BASE_URL:\t{Config.IQAIR_BASE_URL}')
    logger.debug(f'OWM_API_KEY:\t{Config.OWM_API_KEY}')
    logger.debug(f'OWM_ONECALL_BASE_URL:\t{Config.OWM_ONECALL_BASE_URL}')
    logger.debug(f'OWM_GEO_BASE_URL:\t{Config.OWM_GEO_BASE_URL}')
    logger.debug(f'BASE_DIR:\t{Config.BASE_DIR}')
    logger.debug(f'CITY_LIST:\t{Config.CITY_LIST}')
    logger.debug(f'LOG_DIR:\t{Config.LOG_DIR}')
    logger.debug(f'LOG_LEVEL:\t{Config.LOG_LEVEL}')
            
    run_app()
    #run_pipeline()

    logger.info("Air Quality Monitor finished")


if __name__ == "__main__":
    main()