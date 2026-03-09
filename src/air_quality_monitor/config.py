from dotenv import load_dotenv
import os
from pathlib import Path
import json
from .models import City

#load_dotenv(Path(__file__).parent.parent.parent / '.env')  # Load environment variables from .env file

class Config:
    
    load_dotenv() # Load environment variables from .env file

    IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')
    IQAIR_BASE_URL = os.getenv('IQAIR_BASE_URL')
    BASE_DIR = Path(os.getenv('BASE_DIR'))
    DATA_DIR = BASE_DIR / 'data'
    CITY_LIST = Path(os.getenv('CITY_LIST'))

    #print(f'Config loaded: IQAIR_API_KEY={IQAIR_API_KEY}, IQAIR_BASE_URL={IQAIR_BASE_URL}, BASE_DIR={BASE_DIR}, DATA_DIR={DATA_DIR}')

    @classmethod
    def load_cities(cls) -> list[City]:
        with open(cls.CITY_LIST) as f:
            data = json.load(f)
        return [City(**item) for item in data]
