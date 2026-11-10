"""
Application configuration from environment variables.

Loads settings from .env file including API credentials, directory paths,
storage options, and runtime flags (production vs development).
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .models import City


class Config:
    """Central configuration with environment-based settings."""
    load_dotenv()  # Load environment variables from .env file

    # IQAir credentials & URLs
    IQAIR_API_KEY = os.getenv("IQAIR_API_KEY")
    IQAIR_BASE_URL = os.getenv("IQAIR_BASE_URL")

    # OWM credentials & URLs
    OWM_API_KEY = os.getenv("OWM_API_KEY")
    OWM_ONECALL_BASE_URL = os.getenv("OWM_ONECALL_BASE_URL")
    OWM_GEO_BASE_URL = os.getenv("OWM_GEO_BASE_URL")

    # Installation-specific directory structure
    BASE_DIR = Path(os.getenv("BASE_DIR"))
    DATA_DIR = BASE_DIR / "data"
    CONFIG_DIR = BASE_DIR / "config"
    LOG_DIR = BASE_DIR / "log"
    MODELS_DIR = BASE_DIR / "models"
    TRAINING_DATA_PATH = DATA_DIR / "training_data.parquet"

    # How long before HTTP requests time out?
    REQUEST_TIMEOUT = 30

    # Required log level. Defaults to INFO
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Write a log file? Default 'true'
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"

    # Is this a production system?
    IS_PRODUCTION = os.getenv("IS_PRODUCTION", "false").lower() == "true"

    # File with list of cities depends on production flag.
    # If not prod, use a shorter list of cities to save API calls
    city_file = "cities.json" if IS_PRODUCTION else "cities_dev.json"
    CITY_LIST = CONFIG_DIR / city_file

    # Are we saving to CSV? Default 'true'
    USE_CSV = os.getenv("USE_CSV", "true").lower() == "true"

    # Database details
    # Are we using a database? Default 'false'
    USE_DB = os.getenv("USE_DB", "false").lower() == "true"
    if USE_DB:
        DB_TYPE = os.getenv("DB_TYPE")
        DB_USER = os.getenv("DB_USER")
        DB_PASS = os.getenv("DB_PASS")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")

    @classmethod
    def load_cities(cls) -> list[City]:
        """Load city configurations from JSON file."""
        with open(cls.CITY_LIST) as f:
            data = json.load(f)

        return [City(**item) for item in data]

    @classmethod
    def get_db_url(cls) -> str:
        """Build database connection URL from config settings."""
        if cls.DB_TYPE == "sqlite":
            return f"sqlite:///{cls.DATA_DIR}/{cls.DB_NAME}.db"
        else:
            return f"{cls.DB_TYPE}://{cls.DB_USER}:{cls.DB_PASS}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
