from dotenv import load_dotenv
import os
from pathlib import Path
import json
from .models import City

class Config:
        
    load_dotenv() # Load environment variables from .env file

    IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')
    IQAIR_BASE_URL = os.getenv('IQAIR_BASE_URL')

    OWM_API_KEY = os.getenv('OWM_API_KEY')
    OWM_ONECALL_BASE_URL = os.getenv('OWM_ONECALL_BASE_URL')
    OWM_GEO_BASE_URL = os.getenv('OWM_GEO_BASE_URL')

    BASE_DIR = Path(os.getenv('BASE_DIR'))
    #DATA_DIR = Path(BASE_DIR / 'data')
    DATA_DIR = BASE_DIR / 'data'
    #CITY_LIST = Path(os.getenv('CITY_LIST'))
    #CONFIG_DIR = Path(BASE_DIR / 'config')
    CONFIG_DIR = BASE_DIR / 'config'
    #LOG_DIR = Path(BASE_DIR / 'log')
    LOG_DIR = BASE_DIR / 'log'
    LOG_LEVEL = os.getenv('LOG_LEVEL')

    IS_PRODUCTION = os.getenv('IS_PRODUCTION', 'false').lower() == 'true'

    city_file = 'cities.json' if IS_PRODUCTION else 'cities_dev.json'
    CITY_LIST = CONFIG_DIR / city_file

    @classmethod
    def load_cities(cls) -> list[City]:
        try:
            with open(cls.CITY_LIST) as f:
                data = json.load(f)
        except Exception as e:
            raise
        
        return [City(**item) for item in data]
