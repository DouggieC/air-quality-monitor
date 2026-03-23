import logging
from pathlib import Path

from .client import AirQualityClient, WeatherClient
from .config import Config
from .database import Database
from .db_models import DBAirQualityReading, DBWeatherReading
from .logger import setup_logging
from .models import AirQualityReading, WeatherReading
from .parser import AirQualityParser, WeatherParser
from .pipeline import PipelineRunner
from .storage import CSVStorage, DBStorage, JSONStorage


def run_app():
    logger = logging.getLogger(__name__)
    logger.debug("Executing method")

    # Ensure data directory exists
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize API clients
    # aqc = AirQualityClient(Config.IQAIR_API_KEY, Config.IQAIR_BASE_URL)
    wc = WeatherClient(Config.OWM_API_KEY, Config.OWM_ONECALL_BASE_URL, Config.OWM_GEO_BASE_URL)

    aq_csv_filepath = Path(Config.DATA_DIR / "aqi_history.csv")
    aq_csv_storage = CSVStorage(aq_csv_filepath, AirQualityReading)

    we_csv_filepath = Path(Config.DATA_DIR / "we_history.csv")
    we_csv_storage = CSVStorage(we_csv_filepath, WeatherReading)

    db = Database(Config.get_db_url())
    aq_db_storage = DBStorage(db.engine, DBAirQualityReading)
    we_db_storage = DBStorage(db.engine, DBWeatherReading)

    df_aq_csv = aq_csv_storage.read()
    print(f"AQI CSV:\n{df_aq_csv}")
    df_we_csv = we_csv_storage.read()
    print(f"OWM CSV:\n{df_we_csv}")
    df_aq_db = aq_db_storage.read()
    print(f"AQI DB:\n{df_aq_db}")
    df_we_db = we_db_storage.read()
    print(f"OWM DB:\n{df_we_db}")
    exit()

    # Get coordinates for Sarajevo
    cities = Config.load_cities()
    logger.debug(f"Cities:\t{cities}")

    for city in cities:
        # logger.debug(f'Getting coordinates for {city.city}')
        coord_data = wc.get_coordinates(city)
        lat = coord_data.get("lat")
        lon = coord_data.get("lon")
        logger.debug(f"Getting weather data for {city}")
        # weather_data = wc.get_current_weather(city=city)
        # logger.debug(f'Getting AQI data for {city.city}')
        # aqi_data = aqc.get_city_data(city)

        print(f"{city}:\t{lat}, {lon}")

    exit()

    """
        # Get weather for Sarajevo by coords
        print('Getting weather data')
        weather_data = wc.get_current_weather(43.8563, 18.4131)
        #print(weather_data)
        """
    """
    #print(aqc.get_all_countries())
    print(aqc.get_all_states('Switzerland'))
    cities = aqc.get_all_cities('Switzerland', 'Geneva')
    for city in cities:
        print(f'{city}')
    """

    """city = 'Sarajevo'
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
    """


def run_pipeline():

    logger = logging.getLogger(__name__)
    logger.debug("Executing method")

    # Create clients for AQI & OWM, and parsers to format API responses
    aqc = AirQualityClient(Config.IQAIR_API_KEY, Config.IQAIR_BASE_URL)
    wc = WeatherClient(Config.OWM_API_KEY, Config.OWM_ONECALL_BASE_URL, Config.OWM_GEO_BASE_URL)
    aq_parser = AirQualityParser()
    we_parser = WeatherParser()

    # Load the list of cities
    cities = Config.load_cities()
    logger.debug(f"Cities:\t{cities}")

    # Always store the raw JSON data
    aq_json_filepath = Path(Config.DATA_DIR / "aqi_raw_history.jsonl")
    logger.debug(f"JSON filepath: {aq_json_filepath}")
    aq_json_storage = JSONStorage(aq_json_filepath, AirQualityReading)

    we_json_filepath = Path(Config.DATA_DIR / "we_raw_history.jsonl")
    logger.debug(f"JSON filepath: {we_json_filepath}")
    we_json_storage = JSONStorage(we_json_filepath, WeatherReading)

    # If we're storing data in CSV files, set them now.
    if Config.USE_CSV:
        aq_csv_filepath = Path(Config.DATA_DIR / "aqi_history.csv")
        aq_csv_storage = CSVStorage(aq_csv_filepath, AirQualityReading)

        we_csv_filepath = Path(Config.DATA_DIR / "we_history.csv")
        we_csv_storage = CSVStorage(we_csv_filepath, WeatherReading)
    else:
        aq_csv_storage = None
        we_csv_storage = None

    # If we're storing data in a DB, set them now.
    if Config.USE_DB:
        db = Database(Config.get_db_url())
        db.sync_cities(cities)

        aq_db_storage = DBStorage(db.engine, DBAirQualityReading)
        we_db_storage = DBStorage(db.engine, DBWeatherReading)
    else:
        db = None
        aq_db_storage = None
        we_db_storage = None

    # All set up. Let's run the pipeline!
    runner = PipelineRunner(
        aqc,
        wc,
        aq_parser,
        we_parser,
        aq_json_storage=aq_json_storage,
        we_json_storage=we_json_storage,
        aq_csv_storage=aq_csv_storage,
        we_csv_storage=we_csv_storage,
        aq_db_storage=aq_db_storage,
        we_db_storage=we_db_storage,
    )
    runner.run(cities)


def main():

    # Start logging
    setup_logging(log_level=Config.LOG_LEVEL, log_dir=Config.LOG_DIR)
    logger = logging.getLogger(__name__)
    logger.info("Air Quality Monitor started")
    logger.debug("Environment variables:")
    logger.debug(f"IQAIR_API_KEY:\t{Config.IQAIR_API_KEY}")
    logger.debug(f"IQAIR_BASE_URL:\t{Config.IQAIR_BASE_URL}")
    logger.debug(f"OWM_API_KEY:\t{Config.OWM_API_KEY}")
    logger.debug(f"OWM_ONECALL_BASE_URL:\t{Config.OWM_ONECALL_BASE_URL}")
    logger.debug(f"OWM_GEO_BASE_URL:\t{Config.OWM_GEO_BASE_URL}")
    logger.debug(f"BASE_DIR:\t{Config.BASE_DIR}")
    logger.debug(f"DATA_DIR:\t{Config.DATA_DIR}")
    logger.debug(f"CONFIG_DIR:\t{Config.CONFIG_DIR}")
    logger.debug(f"LOG_DIR:\t{Config.LOG_DIR}")
    logger.debug(f"LOG_LEVEL:\t{Config.LOG_LEVEL}")
    logger.debug(f"CITY_LIST:\t{Config.CITY_LIST}")
    logger.debug(f"IS_PRODUCTION:\t{Config.IS_PRODUCTION}")

    # run_app()
    run_pipeline()

    logger.info("Air Quality Monitor finished")


if __name__ == "__main__":
    main()
