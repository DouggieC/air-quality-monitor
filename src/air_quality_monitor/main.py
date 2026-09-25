import argparse
import logging
from pathlib import Path

from .client import AirQualityClient, WeatherClient
from .collector import DataCollector
from .config import Config
from .features import FeatureEngineer
from .logger import setup_logging
from .models import AirQualityReading, DailyForecast, HourlyForecast, WeatherReading
from .parser import AirQualityParser, DailyForecastParser, HourlyForecastParser
from .storage import JSONStorage
from .storage_factory import StorageFactory
from .trainer import Trainer


def run_data_collection():

    logger = logging.getLogger(__name__)
    logger.debug("Executing method")

    # Create clients for AQI & OWM, and parsers to format API responses
    aqc = AirQualityClient(Config.IQAIR_API_KEY, Config.IQAIR_BASE_URL, Config.REQUEST_TIMEOUT)
    wc = WeatherClient(
        Config.OWM_API_KEY, Config.OWM_ONECALL_BASE_URL, Config.OWM_GEO_BASE_URL, Config.REQUEST_TIMEOUT
    )
    aq_parser = AirQualityParser()
    hourly_parser = HourlyForecastParser()
    daily_parser = DailyForecastParser()

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

    # Set up storage
    sf = StorageFactory(Config)
    aq_csv_storage, aq_db_storage = sf.get_storage(AirQualityReading)
    hourly_csv_storage, hourly_db_storage = sf.get_storage(HourlyForecast)
    daily_csv_storage, daily_db_storage = sf.get_storage(DailyForecast)

    # All set up. Let's run the data collection pipeline!
    runner = DataCollector(
        aqc,
        wc,
        aq_parser,
        hourly_parser,
        daily_parser,
        aq_json_storage=aq_json_storage,
        we_json_storage=we_json_storage,
        aq_csv_storage=aq_csv_storage,
        hourly_csv_storage=hourly_csv_storage,
        daily_csv_storage=daily_csv_storage,
        aq_db_storage=aq_db_storage,
        hourly_db_storage=hourly_db_storage,
        daily_db_storage=daily_db_storage,
    )
    runner.run(cities)


def run_feature_engineering():
    logger = logging.getLogger(__name__)
    logger.debug("Executing method")

    # Set up storage
    sf = StorageFactory(Config)
    aqi_csv, aqi_db = sf.get_storage(AirQualityReading)
    we_csv, we_db = sf.get_storage(HourlyForecast)

    # Pick DB or CSV. Prefer DB if both available
    aqi_storage = aqi_db or aqi_csv
    we_storage = we_db or we_csv

    # Run feature engineering
    engineer = FeatureEngineer(aqi_storage, we_storage)
    training_df = engineer.build()
    training_df.to_csv(Config.TRAINING_DATA_PATH, index=False)


def run_training():
    logger = logging.getLogger(__name__)
    logger.debug("Executing method")

    trainer = Trainer()
    trainer.train()


def run_tuning():
    logger = logging.getLogger(__name__)
    logger.debug("Executing method")

    trainer = Trainer()
    trainer.tune()


def main():

    # Start logging
    setup_logging(log_level=Config.LOG_LEVEL, log_dir=Config.LOG_DIR, log_to_file=Config.LOG_TO_FILE)
    logger = logging.getLogger(__name__)
    logger.debug("Environment variables:")
    logger.debug(f"IQAIR_API_KEY:\t{Config.IQAIR_API_KEY}")
    logger.debug(f"IQAIR_BASE_URL:\t{Config.IQAIR_BASE_URL}")
    logger.debug(f"OWM_API_KEY:\t{Config.OWM_API_KEY}")
    logger.debug(f"OWM_ONECALL_BASE_URL:\t{Config.OWM_ONECALL_BASE_URL}")
    logger.debug(f"OWM_GEO_BASE_URL:\t{Config.OWM_GEO_BASE_URL}")
    logger.debug(f"BASE_DIR:\t{Config.BASE_DIR}")
    logger.debug(f"DATA_DIR:\t{Config.DATA_DIR}")
    logger.debug(f"CONFIG_DIR:\t{Config.CONFIG_DIR}")
    logger.debug(f"USE_CSV:\t{Config.USE_CSV}")
    logger.debug(f"USE_DB:\t{Config.USE_DB}")
    logger.debug(f"LOG_DIR:\t{Config.LOG_DIR}")
    logger.debug(f"LOG_LEVEL:\t{Config.LOG_LEVEL}")
    logger.debug(f"LOG_TO_FILE:\t{Config.LOG_TO_FILE}")
    logger.debug(f"CITY_LIST:\t{Config.CITY_LIST}")
    logger.debug(f"IS_PRODUCTION:\t{Config.IS_PRODUCTION}")
    logger.debug(f"REQUEST_TIMEOUT:\t{Config.REQUEST_TIMEOUT}")

    arg_parser = argparse.ArgumentParser(description="Air Quality Monitor")
    arg_parser.add_argument("command", choices=["collect", "prepare", "train", "tune"])
    args = arg_parser.parse_args()

    match args.command:
        case "collect":
            logger.info("Running data collection")
            run_data_collection()
        case "prepare":
            logger.info("Engineering features")
            run_feature_engineering()
        case "train":
            logger.info("Training models")
            run_training()
        case "tune":
            logger.info("Tuning hyperparamters")
            run_tuning()


if __name__ == "__main__":
    main()
