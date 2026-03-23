import logging
from time import sleep

from .client import AirQualityClient, WeatherClient
from .exceptions import APIError, ParseError, StorageError
from .models import City
from .parser import ResponseParser
from .storage import JSONStorage


class PipelineRunner:
    def __init__(
        self,
        aqc: AirQualityClient,
        wc: WeatherClient,
        aq_parser: ResponseParser,
        we_parser: ResponseParser,
        aq_json_storage: JSONStorage,
        we_json_storage: JSONStorage,
        aq_csv_storage=None,
        we_csv_storage=None,
        aq_db_storage=None,
        we_db_storage=None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.aqc = aqc
        self.wc = wc
        self.aq_parser = aq_parser
        self.we_parser = we_parser
        self.aq_json_storage = aq_json_storage
        self.we_json_storage = we_json_storage
        self.aq_csv_storage = aq_csv_storage
        self.we_csv_storage = we_csv_storage
        self.aq_db_storage = aq_db_storage
        self.we_db_storage = we_db_storage

    def run(self, cities: list[City]) -> None:
        # For each city, fetch data, store raw JSON, parse and store structured data as CSV and/or DB
        self.logger.debug("Executing method")

        # Can only make 5 IQAir API calls/min. Count when 5 have been made
        call_count = 0

        for city in cities:
            call_count += 1
            if call_count == 5:
                # Reset the counter to start the next batch of 5 calls and sleep
                call_count = 0
                self.logger.info("Max calls/min reached. Sleeping for 1 minute...")
                sleep(60)

            try:
                # Fetch raw AQI data for city & store it as JSON
                self.logger.info(f"Processing AQI data for city: {city.city}")

                # Record how many API calls we've made
                raw_aq_data = self.aqc.get_city_data(city)
                self.logger.debug(f"Raw data received:\t{raw_aq_data}")
                self.aq_json_storage.save(raw_aq_data)

                # Parse the data ready for storage
                parsed_aq_data = self.aq_parser.parse(raw_aq_data.get("data", {}), city)

                # Write to the CSV file if in use
                if self.aq_csv_storage:
                    self.aq_csv_storage.save(parsed_aq_data)

                # Write to the DB if in use
                if self.aq_db_storage:
                    self.aq_db_storage.save(parsed_aq_data, city)

            except APIError as e:
                self.logger.error(f"Error fetching air quality data for {city.city}: {e}")
            except ParseError as e:
                self.logger.error(f"Error parsing air quality data for {city.city}: {e}")
            except StorageError as e:
                self.logger.error(f"Error saving air quality data for {city.city}: {e}")

            try:
                # Fetch raw OWM data for city & store it as JSON
                self.logger.info(f"Processing OWM data for city: {city.city}")
                raw_we_data = self.wc.get_current_weather(lat=city.latitude, lon=city.longitude)
                self.logger.debug(f"Raw data received:\t{raw_we_data}")
                self.we_json_storage.save(raw_we_data)

                # Parse the data ready for storage
                parsed_we_data = self.we_parser.parse(raw_we_data, city)

                # Write to the CSV file if in use
                if self.we_csv_storage:
                    self.we_csv_storage.save(parsed_we_data)

                # Write to the DB if in use
                if self.we_db_storage:
                    self.we_db_storage.save(parsed_we_data, city)

            except APIError as e:
                self.logger.error(f"Error fetching weather data for {city.city}: {e}")
            except ParseError as e:
                self.logger.error(f"Error parsing weather data for {city.city}: {e}")
            except StorageError as e:
                self.logger.error(f"Error saving weather data for {city.city}: {e}")

            """
            call_count += 1
            if call_count == 5:
                # Reset the counter to start the next batch of 5 calls and sleep
                call_count = 0
                self.logger.info("Max calls/min reached. Sleeping for 1 minute...")
                sleep(60)
            """
