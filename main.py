from config import Config
from client import AirQualityClient
from storage import CSVStorage

def run_app():
    # Load configuration
    config = Config()

    # Initialize API client
    client = AirQualityClient(config.IQAIR_API_KEY, config.IQAIR_BASE_URL)

    # Fetch air quality data (this is a placeholder, implement the actual fetching logic)
    # data = client.fetch_air_quality_data()

    # Initialize storage (using CSV as an example)
    storage = CSVStorage()

def main():
    if __name__ == "__main__":
        run_app()