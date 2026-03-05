from client import AirQualityClient
from storage import BaseStorage
from parser import ResponseParser
from models import City
from exceptions import *
from pathlib import Path

class PipelineRunner:
    def __init__(self, client: AirQualityClient, parser: ResponseParser,
                 raw_storage: BaseStorage, parsed_storage: BaseStorage,
                 data_dir: Path):
        self.client = client
        self.parser = parser
        self.raw_storage = raw_storage
        self.parsed_storage = parsed_storage
        self.data_dir = data_dir

    def run(self, cities: list[City]) -> None:
        # For each city, fetch data, store raw JSON, parse and store structured data

        for city in cities:
            try:
                # Fetch raw data for city & store it as JSON
                print(f'Processing city: {city}')
                raw_data = self.client.get_city_data(city)
                raw_filename = Path(f'{self.data_dir}/{city.city}_raw_history')
                self.raw_storage.save(raw_data, raw_filename)

                # Parse the data and store in structured parquet file
                parsed_data = self.parser.parse(raw_data)
                #print(parsed_data)
                parsed_filename = Path(f'{self.data_dir}/{city.city}_history')
                self.parsed_storage.save(parsed_data, parsed_filename)
            except APIError as e:
                print(f"Error fetching data for city {city}: {e}")
    

