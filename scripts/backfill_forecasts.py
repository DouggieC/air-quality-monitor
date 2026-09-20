import pandas as pd
from sqlalchemy import text

from air_quality_monitor.config import Config
from air_quality_monitor.database import Database
from air_quality_monitor.db_models import DBHourlyForecast

# pd.set_option("display.max_rows", None)
# pd.set_option("display.max_columns", None)

# Begin CSV processing
print("Starting CSV processing")

# Read the data from the CSV file
print("Reading data from data/we_history.csv")
df = pd.read_csv("data/we_history.csv")

# Convert the "dt" and "collected_at" columns to datetime objects in UTC & rename appropriately
print("Preprocessing the DataFrame")
df["dt"] = pd.to_datetime(df["dt"], format="ISO8601", utc=True)
df.rename(columns={"dt": "forecast_for"}, inplace=True)
df["collected_at"] = pd.to_datetime(df["collected_at"], format="ISO8601", utc=True)

# Hourly forecasts don't include sunrise / sunset
df.drop(["sunrise", "sunset"], axis=1, inplace=True)

# Add probability of precipitation column
df["pop"] = 0.0

# Populate missing values for rain, snow, and wind_gust
df["rain"] = df["rain"].fillna(0.0)
df["snow"] = df["snow"].fillna(0.0)
df["wind_gust"] = df["wind_gust"].fillna(df["wind_speed"])

# Reorder the columns nicely
print("Reordering columns in the DataFrame")
df = df[
    [
        "city",
        "state",
        "country",
        "timezone",
        "latitude",
        "longitude",
        "forecast_for",
        "temperature",
        "feels_like",
        "pressure",
        "humidity",
        "dew_point",
        "uvi",
        "clouds",
        "visibility",
        "wind_speed",
        "wind_direction",
        "wind_gust",
        "rain",
        "snow",
        "weather_main",
        "weather_desc",
        "pop",
        "collected_at",
    ]
]

# Create forecasts from df values
print("Creating forecasts from df values")

output_file = "data/hourly_forecast.csv"
first_time = True

# Hours ahead to generate forecasts for
horizons = [1, 2, 4, 8, 12, 24, 48]
forecast_df = pd.DataFrame()

for city in df["city"].unique():
    print(f"Processing city: {city}")
    rows = []
    city_df = df[df["city"] == city].sort_values(by="forecast_for")
    earliest = city_df["forecast_for"].min()

    for _, obs in city_df.iterrows():
        # print(f"Processing observation: {obs['collected_at']} for city: {city}")
        for h in horizons:
            collected_at = obs["forecast_for"] - pd.Timedelta(hours=h)
            if collected_at >= earliest:
                row = obs.copy()
                row["forecast_for"] = obs["forecast_for"]
                row["collected_at"] = collected_at
                rows.append(row)

    print(f"Total rows generated for city {city}: {len(rows)}")

    city_result = pd.DataFrame(rows)
    city_result = city_result.sort_values(by=["collected_at", "forecast_for"]).reset_index(drop=True)
    city_result.to_csv(output_file, mode="a", header=first_time, index=False)

    first_time = False
    del rows, city_result


'''
print(f"Total rows generated: {len(rows)}")
print("Creating DataFrame from rows")
result = pd.DataFrame(rows)
'''

print("Sorting result by collected_at and forecast_for")
result = pd.read_csv(output_file)
result = result.sort_values(by=["collected_at", "forecast_for"]).reset_index(drop=True)
result.to_csv(output_file, index=False)

"""
# Write the result to a new CSV file
print("Writing result to data/hourly_forecast.csv")
result.to_csv("data/hourly_forecast.csv", index=False)
"""

# Begin DB processing
print("Starting database processing")

db = Database(Config.get_db_url())

# Get the list of cities from the database
print("Fetching list of cities from the database")
with db.engine.connect() as connection:
    cities = connection.execute(text("SELECT id, city FROM city")).fetchall()
    city_map = {row.city: row.id for row in cities}

# Map onto the result DataFrame
print("Mapping city names to city IDs in the result DataFrame")
result["city_id"] = result["city"].map(city_map)

# Drop unnecessary columns
print("Dropping unnecessary columns from the result DataFrame")
result.drop(["city", "state", "country", "timezone", "latitude", "longitude"], axis=1, inplace=True)

print(result.head())
print(result.info())

# Create the hourly_forecast table if it doesn't exist
print("Creating the hourly_forecast table if it doesn't exist")
DBHourlyForecast.__table__.create(db.engine, checkfirst=True)

# Write the result to the database
print("Writing result to database")
result.to_sql("hourly_forecast", db.engine, if_exists="append", index=False)

print("Database processing complete")
print("Backfill of hourly forecasts complete")
