from dotenv import load_dotenv
import os

class Config:
    IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')
    IQAIR_BASE_URL = os.getenv('IQAIR_BASE_URL')

