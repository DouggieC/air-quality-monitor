from abc import ABC, abstractmethod
import json
import csv

class BaseStorage(ABC):
    @abstractmethod
    def save(self, reading: str): #AirQualityReading):
        pass

    @abstractmethod
    def fetch(self) -> list[str]: #list[AirQualityReading]:
        pass

class CSVStorage(BaseStorage):
    # A class to handle CSV file storage

    def __init__(self):
        super().__init__()
    
    def save(self, reading: str): #AirQualityReading):
        # Implement CSV saving logic here
        print(f'Saving reading to CSV: {reading}')
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
            # Implement CSV fetching logic here
        pass

class DBStorage(BaseStorage):
    # A class to handle database storage

    def __init__(self):
        super().__init__()
    
    def save(self, reading: str): #AirQualityReading):
        # Implement database saving logic here
        pass
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
        # Implement database fetching logic here
        pass

class ParquetStorage(BaseStorage):
    # A class to handle Parquet file storage

    def __init__(self):
        super().__init__()
    
    def save(self, reading: str): #AirQualityReading):
        # Implement Parquet saving logic here
        pass
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
        # Implement Parquet fetching logic here
        pass

class JSONStorage(BaseStorage):
    # A class to handle JSON file storage

    def __init__(self):
        super().__init__()
    
    def save(self, reading: str): #AirQualityReading):
        # Implement JSON saving logic here
        pass
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
        # Implement JSON fetching logic here
        pass

