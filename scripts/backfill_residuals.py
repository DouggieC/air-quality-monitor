import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path("/home/doug/apps/air-quality-monitor")
DATA_DIR = Path(BASE_DIR / "data")
DB_FILE = Path(DATA_DIR / "air_quality_monitor.db")
CSV_FILE = Path(DATA_DIR / "predictions.csv")

print("Starting residual backfill in DB")
conn = sqlite3.connect(DB_FILE)

print("Getting AQI observations")
aqi_df = pd.read_sql("SELECT city_id, pollutant_timestamp, aqi FROM air_quality_reading", conn)
print("Getting predictions")
pred_df = pd.read_sql("SELECT id, city_id, forecast_for, predicted_aqi FROM prediction", conn)

merged_df = pd.merge(
    aqi_df, pred_df, left_on=["city_id", "pollutant_timestamp"], right_on=["city_id", "forecast_for"]
)

print("Populate actual_aqi & residual")
merged_df["actual_aqi"] = merged_df["aqi"]
merged_df["residual"] = merged_df["actual_aqi"] - merged_df["predicted_aqi"]

updates = merged_df[["actual_aqi", "residual", "id"]].values.tolist()

print("Update DB with new values")
cursor = conn.cursor()
cursor.executemany("UPDATE prediction SET actual_aqi = ?, residual = ? WHERE id = ?", updates)

print("Committing DB changes")
conn.commit()

print("Finished DB migration")

print("Starting CSV migration")
print("Reading data in from DB (SSOT)")
df = pd.read_sql(
    "SELECT city, state, country, timezone, latitude, longitude, "
    "collected_at, forecast_for, predicted_aqi, model_name, horizon, "
    "actual_aqi, residual "
    "FROM prediction "
    "JOIN city ON prediction.city_id = city.id ",
    conn,
)

print("Writing data to CSV")
df.to_csv(CSV_FILE, index=False)

print("Finished CSV migration")
