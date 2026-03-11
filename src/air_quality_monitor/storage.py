from abc import ABC, abstractmethod
from .models import AirQualityReading
import jsonlines
from datetime import datetime
import pandas as pd
from dataclasses import asdict
from pathlib import Path
import logging

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
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating CSVStorage object')
    
    def save(self, reading: AirQualityReading, base_filename: Path):
        # Implement CSV saving logic here
        self.logger.info(f'Saving reading to CSV')
        self.logger.debug(f'Data to be saved: {reading}')
        
        filename = Path(f'{base_filename}.csv')
        self.logger.debug(f'Saving to {filename}')

        df_new = pd.DataFrame([asdict(reading)])

        try:
            df_new.to_csv(
                filename,
                mode='a', # Append to existing file if exists
                header=not filename.exists(),
                index=False
            )
        except Exception as e:
            self.logger.error(f'Error while saving to file: {e}')
            print(f'Error while saving to file: {e}')

        
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
            # Implement CSV fetching logic here
        pass

class DBStorage(BaseStorage):
    # A class to handle database storage

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating DBStorage object')
    
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
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating ParquetStorage object')
    
    def save(self, reading: AirQualityReading, base_filename: Path):
        
        filename = Path(f'{base_filename}.parquet')

        # Can't append to a parquet file. Need to read to DF, combine with new and write back
        df_new = pd.DataFrame([asdict(reading)])

        if filename.exists():
            df_history = pd.read_parquet(filename)
            df_combined = pd.concat([df_history, df_new], ignore_index=True)
        else:
            df_combined = df_new
        
        df_combined.to_parquet(filename, index=False)
    
    def fetch(self) -> list[AirQualityReading]:
        # Implement Parquet fetching logic here
        pass

class JSONStorage(BaseStorage):
    # A class to handle JSON file storage

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating JSONStorage object')
    
    def _normalise(self, obj) -> object:
        # Normalise all data to be JSON-serialisable
        self.logger.debug('Executing _normalise')

        # No problem here - just return the object as-is
        if obj is None or isinstance(obj, (str, int, float, bool)):
            self.logger.debug('Basic type or empty')
            return obj
        
        # Convert datetime to ISO format string
        if isinstance(obj, datetime):
            self.logger.debug('Datetime object. Converting to ISO format')
            return obj.isoformat()
        
        # Recurse to convert all values in dicts
        if isinstance(obj, dict):
            self.logger.debug('Dict. Recursing for all values')
            return {k: self._normalise(v) for k, v in obj.items()}
        
        # Same for lists, tuples & sets
        if isinstance(obj, (list, tuple, set)):
            self.logger.debug('List, tuple or set. Recursing for all values')
            return [self._normalise(v) for v in obj]
        
        # dataclasses: convert to dict & recurse
        from dataclasses import is_dataclass, asdict
        if is_dataclass(obj):
            self.logger.debug('Dataclass. Recursing for all values')
            return self._normalise(asdict(obj))
        
        # Run out of ideas. Just convert to string and cross fingers
        return str(obj)
    
    def save(self, reading: AirQualityReading, base_filename: Path):
        
        self.logger.info(f'Saving raw data to JSON')
        self.logger.debug(f'Data to be saved: {reading}')
        
        filename = Path(f'{base_filename}.jsonl')
        self.logger.debug(f'Saving to {filename}')

        reading_json = self._normalise(reading)
        
        try:
            with jsonlines.open(filename, mode='a') as writer:
                writer.write(reading_json)
        except Exception as e:
            self.logger.error(f'Error while saving to file: {e}')
            print(f'Error while saving to file: {e}')


        
    
    def fetch(self) -> list[str]: #list[AirQualityReading]:
        # Implement JSON fetching logic here
        pass

