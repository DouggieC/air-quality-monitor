import pandas as pd

print("Fixing CSVs")

DATA_DIR = "/home/doug/apps/air-quality-monitor/data"

print("Reading data")
aqi_source = pd.read_csv(f"{DATA_DIR}/aqi_history.csv")
we_source = pd.read_csv(f"{DATA_DIR}/hourly_forecast.csv")

# we_source is corrupt in later rows. Find start of corruption
print("Identifying start of corruption in OWM data")
mask = we_source["temperature"].str.startswith("2026")

first_idx = mask.idxmax()
print(f"First bad row at index:\t{first_idx}")
we_source_good = we_source.iloc[:first_idx].reset_index(drop=True)
we_source_bad = we_source.iloc[first_idx:].reset_index(drop=True)

print("Renaming OWM columns to match data in corrupt OWM rows")
we_source_bad = we_source_bad.rename(
    columns={
        "temperature": "collected_at",
        "feels_like": "temperature",
        "pressure": "feels_like",
        "humidity": "pressure",
        "dew_point": "humidity",
        "uvi": "dew_point",
        "clouds": "uvi",
        "visibility": "clouds",
        "wind_speed": "visibility",
        "wind_direction": "wind_speed",
        "wind_gust": "wind_direction",
        "rain": "wind_gust",
        "snow": "rain",
        "pop": "weather_main",
        "collected_at": "weather_desc",
        "weather_main": "pop",
        "weather_desc": "snow",
    }
)

print("Rearranging columns in corrupted OWM data")
we_source_bad = we_source_bad.reindex(
    [
        "city",
        "state",
        "country",
        "timezone",
        "latitude",
        "longitude",
        "collected_at",
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
        "pop",
        "rain",
        "snow",
        "weather_main",
        "weather_desc",
    ],
    axis="columns",
)

print("Rearranging columns in good OWM data")
we_source_good = we_source_good.reindex(
    [
        "city",
        "state",
        "country",
        "timezone",
        "latitude",
        "longitude",
        "collected_at",
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
        "pop",
        "rain",
        "snow",
        "weather_main",
        "weather_desc",
    ],
    axis="columns",
)

print("Joining good and fixed OWM data")
we_source_new = pd.concat([we_source_good, we_source_bad], ignore_index=True)

print("Saving fixed OWM data")
we_source_new.to_csv(f"{DATA_DIR}/hourly_forecast_new.csv")

print("Reordering columns in AQI data")
aqi_source = aqi_source.reindex(
    [
        "city",
        "state",
        "country",
        "timezone",
        "latitude",
        "longitude",
        "collected_at",
        "aqi",
        "main_pollutant",
        "pollutant_timestamp",
        "temperature",
        "humidity",
        "pressure",
        "wind_speed",
        "wind_direction",
        "heat_index",
        "weather_timestamp",
    ],
    axis="columns",
)

print("Saving reordered AQI data")
aqi_source.to_csv(f"{DATA_DIR}/aqi_history_new.csv")
