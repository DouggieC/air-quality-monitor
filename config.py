from dotenv import load_dotenv
import os

class Config:
    load_dotenv()  # Load environment variables from .env file
    
    IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')
    IQAIR_BASE_URL = os.getenv('IQAIR_BASE_URL')

    print(f'Config loaded: IQAIR_API_KEY={IQAIR_API_KEY}, IQAIR_BASE_URL={IQAIR_BASE_URL}')

