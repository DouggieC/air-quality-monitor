import logging

from .database import Database
from .db_models import DBAirQualityReading, DBDailyForecast, DBHourlyForecast, DBWeatherReading
from .models import AirQualityReading, DailyForecast, HourlyForecast, WeatherReading
from .storage import CSVStorage, DBStorage


class StorageFactory:
    def __init__(self, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.config = config
        self._db = None

        # Registry: model_class -> (CSV filename, DB model class)
        self.registry = {
            AirQualityReading: ("aqi_history.csv", DBAirQualityReading),
            WeatherReading: ("we_history.csv", DBWeatherReading),
            HourlyForecast: ("hourly_forecast.csv", DBHourlyForecast),
            DailyForecast: ("daily_forecast.csv", DBDailyForecast),
        }

    @property
    def db(self):
        if self._db is None and self.config.USE_DB:
            self.logger.debug("Initializing database connection")
            self._db = Database(self.config.get_db_url())
        return self._db

    def get_storage(self, model_class):
        self.logger.debug("Executing method")

        if model_class not in self.registry:
            raise ValueError(f"Model class {model_class} not registered in storage factory.")

        csv_filename, db_model_class = self.registry[model_class]

        csv_storage = None
        db_storage = None

        if self.config.USE_CSV:
            self.logger.debug(f"Creating CSV storage for {model_class.__name__} with filename {csv_filename}")
            csv_storage = CSVStorage(self.config.DATA_DIR / csv_filename, model_class)

        if self.config.USE_DB and self.db:
            self.logger.debug(f"Creating DB storage for {model_class.__name__}")
            db_storage = DBStorage(self.db.engine, db_model_class)

        return csv_storage, db_storage
