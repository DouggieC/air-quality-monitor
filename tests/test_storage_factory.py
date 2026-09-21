import pytest

from air_quality_monitor.config import Config
from air_quality_monitor.models import AirQualityReading
from air_quality_monitor.storage import CSVStorage, DBStorage
from air_quality_monitor.storage_factory import StorageFactory


class TestStorageFactory:
    @pytest.fixture
    def mock_config(self, tmp_path) -> Config:
        config = Config()
        config.DATA_DIR = tmp_path
        config.USE_CSV = True
        config.USE_DB = True
        config.get_db_url = lambda: "sqlite:///:memory:"
        return config

    def test_get_storage_csv_only(self, mock_config):
        mock_config.USE_DB = False
        factory = StorageFactory(mock_config)

        csv_storage, db_storage = factory.get_storage(AirQualityReading)

        assert isinstance(csv_storage, CSVStorage)
        assert db_storage is None

    def test_get_storage_db_only(self, mock_config):
        mock_config.USE_CSV = False
        factory = StorageFactory(mock_config)

        csv_storage, db_storage = factory.get_storage(AirQualityReading)

        assert csv_storage is None
        assert isinstance(db_storage, DBStorage)

    def test_get_storage_both(self, mock_config):
        factory = StorageFactory(mock_config)

        csv_storage, db_storage = factory.get_storage(AirQualityReading)

        assert isinstance(csv_storage, CSVStorage)
        assert isinstance(db_storage, DBStorage)
