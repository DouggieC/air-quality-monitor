from client import AirQualityClient
from storage import BaseStorage
from parser import ResponseParser


class PipelineRunner:
    def __init__(self, client: AirQualityClient, parser: ResponseParser,
                 raw_storage: BaseStorage, parsed_storage: BaseStorage):
        self.client = client
        self.parser = parser
        self.raw_storage = raw_storage
        self.parsed_storage = parsed_storage

    def run(self, cities: list[str]) -> None:
        # For each city, fetch data, store raw JSON, parse and store structured data
        
        for city in cities:
            try:
                # Fetch raw data for city & store it as JSON
                print(f'Processing city: {city}')
                raw = self.client.get_city_data(city)
                self.raw_storage.save(raw, f'{city}_raw_history')

                # Parse the data and store in structured parquet file
                parsed_data = self.parser.parse(raw)
                self.parsed_storage.save(parsed_data)
            except Exception as e:
                print(f"Error fetching data for city {city}: {e}")
    

