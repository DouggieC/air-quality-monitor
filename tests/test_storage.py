from dataclasses import asdict
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from air_quality_monitor.db_models import Base, DBAirQualityReading, DBCity
from air_quality_monitor.models import AirQualityReading, City
from air_quality_monitor.storage import CSVStorage, DBStorage


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
        pd.testing.assert_frame_equal(df_save, df_read, check_dtype=False)

    def test_read(self, csv_storage: CSVStorage, sample_aqr: AirQualityReading):

        # Create a file to read from
        df_save = pd.DataFrame([asdict(sample_aqr)])
        df_save.to_csv(csv_storage.filepath, index=False)

        df_read = csv_storage.read()

        pd.testing.assert_frame_equal(df_read, df_save, check_dtype=False)


class TestDBStorage:
    @pytest.fixture
    def db_storage(self, engine: Engine, sample_aqr, sample_city) -> DBStorage:

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
                    latitude=sample_city.latitude,
                    longitude=sample_city.longitude,
                )
            )
            session.commit()

        aq_db = DBStorage(engine, DBAirQualityReading)

        return aq_db

    def test_save(
        self, db_storage: DBStorage, sample_aqr: AirQualityReading, city: City
    ):
        pass
