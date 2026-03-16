import logging
from  time import sleep
from .client import AirQualityClient, WeatherClient
from .storage import BaseStorage
from .parser import ResponseParser
from .models import City
from .exceptions import *
from pathlib import Path

class PipelineRunner:
    def __init__(self, aqc: AirQualityClient, wc: WeatherClient,
                 aq_parser: ResponseParser, we_parser: ResponseParser,
                 raw_storage: BaseStorage, parsed_storage: BaseStorage,
                 data_dir: Path):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f'Creating object')
        self.aqc = aqc
        self.wc = wc
        self.aq_parser = aq_parser
        self.we_parser = we_parser
        self.raw_storage = raw_storage
        self.parsed_storage = parsed_storage
        self.data_dir = data_dir

    def run(self, cities: list[City]) -> None:
        # For each city, fetch data, store raw JSON, parse and store structured data as CSV
        self.logger.debug('Executing method')

        # Can only make 5 IQAir API calls/min. Count when 5 have been made
        call_count = 0

        for city in cities:
            try:
                # Fetch raw AQI data for city & store it as JSON
                self.logger.info(f'Processing AQI data for city: {city.city}')
                raw_data = self.aqc.get_city_data(city)
                self.logger.debug(f'Raw data received:\t{raw_data}')
                raw_filename = Path(f'{self.data_dir}/aqi_raw_history')
                self.raw_storage.save(raw_data, raw_filename)

                # Parse the data and store in structured CSV file
                parsed_aq_data = self.aq_parser.parse(raw_data.get('data', {}), city)
                parsed_aq_filename = Path(f'{self.data_dir}/aqi_history')
                self.parsed_storage.save(parsed_aq_data, parsed_aq_filename)
            except APIError as e:
                self.logger.error(f"Error fetching air quality data for {city.city}: {e}")

            try:
                # Fetch raw OWM data for city & store it as JSON
                self.logger.info(f'Processing OWM data for city: {city.city}')
                #raw_data = self.wc.get_current_weather(city=city)
                raw_data = self.wc.get_current_weather(lat=city.latitude, lon=city.longitude)
                self.logger.debug(f'Raw data received:\t{raw_data}')
                raw_filename = Path(f'{self.data_dir}/we_raw_history')
                self.raw_storage.save(raw_data, raw_filename)

                # Parse the data and store in structured CSV file
                parsed_aq_data = self.we_parser.parse(raw_data, city)
                parsed_aq_filename = Path(f'{self.data_dir}/we_history')
                self.parsed_storage.save(parsed_aq_data, parsed_aq_filename)
            except APIError as e:
                self.logger.error(f"Error fetching weather data for {city.city}: {e}")
            
            call_count += 1
            if call_count == 5:
                # Reset the counter to start the next batch of 5 calls and sleep
                call_count = 0
                self.logger.info('Max calls/min reached. Sleeping for 1 minute...')
                sleep(60)
            


                

    

