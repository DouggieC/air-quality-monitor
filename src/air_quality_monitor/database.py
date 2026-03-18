import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .db_models import Base, DBCity
from .models import City


class Database:
    def __init__(self, db_url: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")

        self.logger.info(f"Initialising DB:\t{db_url}")
        self.engine = self.get_engine(db_url)
        self.logger.debug("Initialising tables")
        Base.metadata.create_all(self.engine)
        self.logger.info("Database initialised")

    def get_engine(self, db_url: str):
        self.logger.debug("Executing method")
        return create_engine(db_url)

    def init_db(self, db_url, str):
        self.logger.debug("Executing method")
        engine = self.get_engine(db_url)
        Base.metadata.create_all(engine)
        return engine

    # def sync_cities(self, engine, cities: list[City]):
    def sync_cities(self, cities: list[City]):
        self.logger.debug("Executing method")

        with Session(self.engine) as session:
            for city in cities:
                # Add city to table if not already there
                self.logger.debug(f"Checking for {city.city}")
                exists = (
                    session.query(DBCity)
                    .filter_by(city=city.city, country=city.country)
                    .first()
                )

                if not exists:
                    self.logger.debug(f"{city.city} not found. Adding to table...")
                    session.add(
                        DBCity(
                            city=city.city,
                            state=city.state,
                            country=city.country,
                            latitude=city.latitude,
                            longitude=city.longitude,
                        )
                    )
                else:
                    self.logger.debug(f"{city.city} already exists: {exists}")

            session.commit()
