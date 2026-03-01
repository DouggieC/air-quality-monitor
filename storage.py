from abc import ABC, abstractmethod
from client import AirQualityReading
import json
import jsonlines
import csv
from datetime import datetime

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
    
    def _normalise(self, obj) -> object:
        # Normalise all data to be JSON-serialisable

        # No problem here - just return the object as-is
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        
        # Convert datetime to ISO format string
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Recurse to convert all values in dicts
        if isinstance(obj, dict):
            return {k: self._normalise(v) for k, v in obj.items()}
        
        # Same for lists, tuples & sets
        if isinstance(obj, (list, tuple, set)):
            return [self._normalise(v) for v in obj]
        
        # dataclasses: convert to dict & recurse
        from dataclasses import is_dataclass, asdict
        if is_dataclass(obj):
            return self._normalise(asdict(obj))
        
        # Run out of ideas. Just convert to string and cross fingers
        return str(obj)
    
    def save(self, reading: AirQualityReading, base_filename):
        # Implement JSON saving logic here
        filename = f'{base_filename}.jsonl'
        reading_json = self._normalise(reading)
        print(f'Saving reading to JSONL: {reading_json} (filename={filename})')
        with jsonlines.open(filename, mode='a') as writer:
            writer.write(reading_json)

        
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
        # Implement JSON fetching logic here
        pass

