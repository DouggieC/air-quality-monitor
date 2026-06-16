import csv
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path

import jsonlines
import pandas as pd
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from .db_models import Base, DBCity
from .models import City, Reading


class BaseStorage(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")

    @abstractmethod
    def save(self, reading: Reading):
        pass

    @abstractmethod
    def read(self) -> list[str]:
        pass


class FileStorage(BaseStorage):
    def __init__(self, filepath: Path, model_class):
        super().__init__()

        self.filepath = filepath
        self.model_class = model_class

        if not issubclass(self.model_class, Reading):
            raise ValueError(f"{self.model_class} is not a valid Reading model")

    def _get_datetime_cols(self) -> list[str]:
        dates = [f.name for f in fields(self.model_class) if f.type == datetime]
        self.logger.debug(f"Datetime columns: {dates}")
        return dates
        #return [f.name for f in fields(self.model_class) if f.type == datetime]


class CSVStorage(FileStorage):
    # A class to handle CSV file storage

    def __init__(self, filepath: Path, model_class):
        super().__init__(filepath, model_class)

    def save(self, reading: Reading) -> None:
        # Implement CSV saving logic here
        self.logger.debug("Executing method")
        self.logger.info("Saving reading to CSV")
        self.logger.debug(f"Data to be saved: {reading}")
        self.logger.debug(f"Saving to {self.filepath}")

        df_new = pd.DataFrame([asdict(reading)])

        try:
            df_new.to_csv(
                self.filepath,
                mode="a",  # Append to existing file if exists
                header=not self.filepath.exists(),
                index=False,
                quoting=csv.QUOTE_NONNUMERIC,
            )
        except Exception as e:
            self.logger.error(f"Error while saving to file: {e}")

    def read(self) -> pd.DataFrame:
        # Read the specified CSV file into a dataframe
        self.logger.debug("Executing method")
        self.logger.info(f"Reading CSV file {self.filepath}")

        if not self.filepath.exists():
            self.logger.error(f"File not found: {self.filepath}")
            raise FileNotFoundError(f"File not found: {self.filepath}")

        try:
            df = pd.read_csv(self.filepath, parse_dates=self._get_datetime_cols())
        except Exception as e:
            self.logger.error(f"Error reading {self.filepath}: {e}")
            raise

        # Make sure datetime objects are correctly typed
        for col in self._get_datetime_cols():
            if df[col].dtype != 'datetime64':
                df[col] = pd.to_datetime(df[col], utc=True, format='ISO8601')


        self.logger.debug(f"DataFrame created:\n{df}")
        return df


class JSONStorage(FileStorage):
    # A class to handle JSON file storage

    def __init__(self, filepath: Path, model_class):
        super().__init__(filepath, model_class)

    def _normalise(self, obj) -> object:
        # Normalise all data to be JSON-serialisable
        self.logger.debug("Executing _normalise")

        # No problem here - just return the object as-is
        if obj is None or isinstance(obj, (str, int, float, bool)):
            self.logger.debug("Basic type or empty")
            return obj

        # Convert datetime to ISO format string
        if isinstance(obj, datetime):
            self.logger.debug("Datetime object. Converting to ISO format")
            return obj.isoformat()

        # Recurse to convert all values in dicts
        if isinstance(obj, dict):
            self.logger.debug("Dict. Recursing for all values")
            return {k: self._normalise(v) for k, v in obj.items()}

        # Same for lists, tuples & sets
        if isinstance(obj, (list, tuple, set)):
            self.logger.debug("List, tuple or set. Recursing for all values")
            return [self._normalise(v) for v in obj]

        # dataclasses: convert to dict & recurse
        from dataclasses import asdict, is_dataclass

        if is_dataclass(obj):
            self.logger.debug("Dataclass. Recursing for all values")
            return self._normalise(asdict(obj))

        # Run out of ideas. Just convert to string and cross fingers
        return str(obj)

    def save(self, reading: Reading) -> None:

        self.logger.debug("Executing method")
        self.logger.info("Saving raw data to JSON")
        self.logger.debug(f"Data to be saved: {reading}")
        self.logger.debug(f"Saving to {self.filepath}")

        reading_json = self._normalise(reading)

        try:
            with jsonlines.open(self.filepath, mode="a") as writer:
                writer.write(reading_json)
        except Exception as e:
            self.logger.error(f"Error while saving to file: {e}")

    def read(self) -> list[str]:  # list[AirQualityReading]:
        # Implement JSON fetching logic here
        pass


class DBStorage(BaseStorage):
    # A class to handle database storage

    def __init__(self, engine: Engine, model_class):
        super().__init__()
        # self.logger = logging.getLogger(self.__class__.__name__)
        # self.logger.debug("Creating object")

        self.engine = engine
        self.model_class = model_class

        if not issubclass(self.model_class, Base):
            raise ValueError(f"{self.model_class} is not a valid SQLAlchemy model")

    def save(self, reading: Reading, city: City):
        # Write to the table
        self.logger.debug("Executing method")
        self.logger.info("Saving reading to DB")

        reading_dict = asdict(reading)
        self.logger.debug(f"Data to be saved (dictionary): {reading_dict}")

        try:
            with Session(self.engine) as session:
                # Get city_id from the database
                db_city = (
                    session.query(DBCity)
                    .filter_by(city=city.city, state=city.state, country=city.country)
                    .first()
                )
                if db_city is None:
                    raise ValueError(f"{city.city} not found in database")
                self.logger.debug(f"Found city:\t{db_city}")

                # Remove city data...
                # for key in ["city", "state", "country", "latitude", "longitude"]:
                city_keys = {f.name for f in fields(City)}
                for key in city_keys:
                    self.logger.debug(f"Popping key {key}")
                    reading_dict.pop(key, None)

                # ...and add the city_id FK instead
                reading_dict["city_id"] = db_city.id
                self.logger.debug(f"reading as dict with city_id: {reading_dict}")

                # Create the DB class
                data = self.model_class(**reading_dict)

                # and add it to the session
                session.add(data)
                session.commit()
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            raise

    def read(self) -> pd.DataFrame:
        # Implement database fetching logic here

        try:
            query = select(self.model_class, DBCity.timezone).join(DBCity)
            df = pd.read_sql(query, self.engine)
        except Exception as e:
            self.logger.error(f"Error reading from database: {e}")
            raise

        for col in df.select_dtypes(include="datetime64"):
            if df[col].dt.tz is None:
                df[col] = df[col].dt.tz_localize("UTC")

        return df


class ParquetStorage(FileStorage):
    # A class to handle Parquet file storage
    # NOT YET IMPLEMENTED

    def __init__(self, filepath: Path, model_class):
        super().__init__(filepath, model_class)

        self.not_implemented_msg = "Parquet storage is not yet implemented. Use CSV or DB instead."
        self.logger.warning(self.not_implemented_msg)

        if not issubclass(self.model_class, Base):
            raise ValueError(f"{self.model_class} is not a valid SQLAlchemy model")

    def save(self, reading: Reading, base_filename: Path):
        raise NotImplementedError(self.not_implemented_msg)

    def fetch(self) -> list[Reading]:
        # Implement Parquet fetching logic here
        raise NotImplementedError(self.not_implemented_msg)
