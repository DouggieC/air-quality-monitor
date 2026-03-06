from dotenv import load_dotenv
import os
from pathlib import Path

class Config:
    load_dotenv()  # Load environment variables from .env file
    
    IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')
    IQAIR_BASE_URL = os.getenv('IQAIR_BASE_URL')
    BASE_DIR = Path(os.getenv('BASE_DIR'))
    DATA_DIR = BASE_DIR / 'data'

    print(f'Config loaded: IQAIR_API_KEY={IQAIR_API_KEY}, IQAIR_BASE_URL={IQAIR_BASE_URL}, BASE_DIR={BASE_DIR}, DATA_DIR={DATA_DIR}')

