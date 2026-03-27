import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from air_quality_monitor.db_models import Base, DBAirQualityReading, DBCity
from air_quality_monitor.models import AirQualityReading, City
from air_quality_monitor.storage import CSVStorage, DBStorage, JSONStorage


class TestCSVStorage:
    @pytest.fixture
    def csv_storage(self, tmp_path: Path) -> CSVStorage:

        aq_csv_file = tmp_path / "aq_test.csv"
        aq_csv = CSVStorage(aq_csv_file, AirQualityReading)

        return aq_csv

    def test_save(self, csv_storage: CSVStorage, sample_aqr: AirQualityReading):

        file = csv_storage.filepath

        aqr = sample_aqr
        csv_storage.save(aqr)
        assert file.exists()

        df_save = pd.DataFrame([asdict(aqr)])
        df_read = pd.read_csv(file)
        df_read["pollutant_timestamp"] = pd.to_datetime(df_read["pollutant_timestamp"], utc=True)
        df_read["weather_timestamp"] = pd.to_datetime(df_read["weather_timestamp"], utc=True)
        df_read["collected_at"] = pd.to_datetime(df_read["collected_at"], utc=True)
        pd.testing.assert_frame_equal(df_save, df_read, check_dtype=False)

    def test_read(self, csv_storage: CSVStorage, sample_aqr: AirQualityReading):

        # Create a file to read from
        df_save = pd.DataFrame([asdict(sample_aqr)])
        df_save.to_csv(csv_storage.filepath, index=False)

        # Do the read
        df_read = csv_storage.read()

        pd.testing.assert_frame_equal(df_read, df_save, check_dtype=False)


class TestDBStorage:
    @pytest.fixture
    def db_storage(self, sample_aqr: AirQualityReading, sample_city: City) -> DBStorage:

        # Create the DB engine and all tables
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        # Set up dummy city table
        with Session(engine) as session:
            session.add(
                DBCity(
                    city=sample_city.city,
                    state=sample_city.state,
                    country=sample_city.country,
                    timezone=sample_city.timezone,
                    latitude=sample_city.latitude,
                    longitude=sample_city.longitude,
                )
            )
            session.commit()

        aq_db = DBStorage(engine, DBAirQualityReading)

        return aq_db

    def test_save(self, db_storage: DBStorage, sample_aqr: AirQualityReading, sample_city: City):

        # Write a row of data to the DB
        db_storage.save(sample_aqr, sample_city)

        # Check it's written by querying it back
        with Session(db_storage.engine) as session:
            row = session.query(DBAirQualityReading).first()

        # Did it get written at all?
        assert row is not None

        # Does numeric & string data make the round trip correctly?
        assert row.aqi == sample_aqr.aqi
        assert row.main_pollutant == sample_aqr.main_pollutant
        assert row.wind_speed == sample_aqr.wind_speed

        # SQLite has problems with datetime formats. Skipping that test.
        # assert row.pollutant_timestamp == sample_aqr.pollutant_timestamp

    def test_read(self, db_storage: DBStorage, sample_aqr: AirQualityReading):

        # Write some data to read from
        with Session(db_storage.engine) as session:
            city = session.query(DBCity).first()
            city_id = city.id

            row_dict = asdict(sample_aqr)
            row_dict["city_id"] = city_id
            for key in ["city", "state", "country", "latitude", "longitude"]:
                row_dict.pop(key)

            session.add(DBAirQualityReading(**row_dict))
            session.commit()

        # Read the data back
        df_read = db_storage.read()

        # Did we get anything back?
        assert df_read is not None

        # Does numeric & string data make the round trip correctly?
        assert df_read.iloc[0]["aqi"] == sample_aqr.aqi
        assert df_read.iloc[0]["main_pollutant"] == sample_aqr.main_pollutant
        assert df_read.iloc[0]["wind_speed"] == sample_aqr.wind_speed


class TestJSONStorage:
    @pytest.fixture
    def sample_aqr_json(self) -> str:
        return '{"status": "success", "data": {"city": "Sarajevo", "state": "Federation of B&H", "country": "Bosnia Herzegovina", "location": {"type": "Point", "coordinates": [18.3972, 43.8559]}, "current": {"pollution": {"ts": "2026-03-19T16:00:00.000Z", "aqius": 63, "mainus": "p2", "aqicn": 24, "maincn": "p1"}, "weather": {"ts": "2026-03-19T16:00:00.000Z", "ic": "04d", "hu": 47, "pr": 1016, "tp": 7, "wd": 60, "ws": 4.17, "heatIndex": 7}}}}'

    @pytest.fixture
    def json_storage(self, tmp_path: Path) -> JSONStorage:

        aq_json_file = tmp_path / "aq_test.jsonl"
        aq_json = JSONStorage(aq_json_file, AirQualityReading)

        return aq_json

    def test_save(self, json_storage: JSONStorage, sample_aqr_json: str):

        file = json_storage.filepath

        json_storage.save(sample_aqr_json)

        # Did anything get written?
        assert file.exists()

        # Can we get the data back?
        with open(file) as f:
            data = json.load(f)

        # assert data == aqr
        assert data == sample_aqr_json

    def test_read(self, json_storage: JSONStorage):
        pass
