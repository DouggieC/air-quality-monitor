import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from air_quality_monitor.config import Config
from air_quality_monitor.database import Database
from air_quality_monitor.db_models import DBAirQualityReading, DBCity, DBWeatherReading
from air_quality_monitor.logger import setup_logging
from air_quality_monitor.models import Reading
from air_quality_monitor.storage import CSVStorage


class Migrator:
    def __init__(self):
        """
        Set up migration and create DB engine.
        Does this truncate the DB? This is the place to do it if not
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")

        self.db = Database(Config.get_db_url())

    def delete_all_data(self):
        """
        Delete all data from the database before loading in the CSV data
        WARNING: Permanently deletes all data from the database. Only run before initial migration.
        """
        self.logger.debug("Executing method")

        try:
            with Session(self.db.engine) as session:
                session.query(DBAirQualityReading).delete()
                session.query(DBWeatherReading).delete()
                session.query(DBCity).delete()
                session.commit()
        except Exception as e:
            self.logger.error(f"Error deleting from database: {e}")
            raise

    def migrate_aqi_data(self, city_lookup: dict):
        self.logger.debug("Executing method")

        self._migrate_data("aqi_history.csv", "air_quality_reading", city_lookup)

    def migrate_weather_data(self, city_lookup: dict):
        self.logger.debug("Executing method")

        self._migrate_data("we_history.csv", "weather_reading", city_lookup)

    def build_city_lookup(self, cities) -> dict:
        """
        For all cities, look up the index in the DB to provide FKs
        """
        self.logger.debug("Executing method")

        city_lookup = {}

        with Session(self.db.engine) as session:
            for city in cities:
                index = session.query(DBCity.id).filter_by(city=city.city, country=city.country).scalar()
                city_lookup[city.city] = index

        return city_lookup

    def count_rows(self, table) -> int:
        self.logger.debug("Executing method")
        with Session(self.db.engine) as session:
            return session.query(table).count()

    def _save_to_database(self, df: pd.DataFrame, table_name: str):
        self.logger.debug("Executing method")

        try:
            df.to_sql(name=table_name, con=self.db.engine, if_exists="append", index=False)
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            raise

    def _migrate_data(self, filename: str, table_name: str, city_lookup: dict):
        self.logger.debug("Executing method")

        csv_filepath = Path(Config.DATA_DIR / filename)
        csv_storage = CSVStorage(csv_filepath, Reading)
        df = csv_storage.read()

        # Add city FK
        df["city_id"] = df["city"].map(city_lookup)

        # Check we have a city for every row
        bad_rows = df[df["city_id"].isna()]
        if not bad_rows.empty:
            raise ValueError(f"Bad city name found at index {bad_rows.index}: {bad_rows['city']}")

        # Drop city columns replaced by FK
        df = df.drop(["city", "state", "country", "timezone", "latitude", "longitude"], axis=1)

        self._save_to_database(df, table_name)


def main():
    setup_logging(log_level=Config.LOG_LEVEL, log_dir=Config.LOG_DIR)
    logger = logging.getLogger(__name__)
    logger.info("Database migration started")

    migrator = Migrator()

    # Clear any data from the database
    logger.info("Deleting data from database")
    migrator.delete_all_data()
    logger.info("Data deleted successfully")

    # Populate the City table from cities.json
    logger.info("Populating city table")
    cities = Config.load_cities()
    migrator.db.sync_cities(cities)
    logger.info(f"Added {migrator.count_rows(DBCity)} cities")
    city_lookup = migrator.build_city_lookup(cities)

    # Populate with AQI data from CSV
    logger.info("Populating air_quality_reading table")
    migrator.migrate_aqi_data(city_lookup)
    logger.info(f"Added {migrator.count_rows(DBAirQualityReading)} rows")

    # Populate with weather data from CSV
    logger.info("Populating weather_reading table")
    migrator.migrate_weather_data(city_lookup)
    logger.info(f"Added {migrator.count_rows(DBWeatherReading)} rows")


if __name__ == "__main__":
    main()
